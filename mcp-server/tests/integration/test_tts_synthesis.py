import io
import wave
import sys
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

# Dynamically load tts/app.py with its dependencies
tts_dir = Path(__file__).resolve().parents[3] / "tts"
sys.path.insert(0, str(tts_dir))

tts_app_path = tts_dir / "app.py"
spec = importlib.util.spec_from_file_location("tts_service_app", str(tts_app_path))
tts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts_module)

tts_app = tts_module.app
engine = tts_module.engine

def test_tts_model_loading():
    """Verify CosyVoice engine model loading and readiness."""
    assert engine.model_loaded is True
    assert engine.device in ["cpu", "cuda"]
    assert engine.sample_rate == 22050
    assert engine.model_manager.is_model_downloaded() or engine.model_manager.model_path.exists()

def test_tts_health_probe():
    """Verify TTS health endpoint."""
    client = TestClient(tts_app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_tts_status_probe():
    """Verify TTS status endpoint reports cosyvoice provider."""
    client = TestClient(tts_app)
    res = client.get("/status")
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "cosyvoice"
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert "device" in data

def test_tts_text_synthesis_and_real_audio_output(tmp_path):
    """
    PASS CRITERIA: A real audio file is produced locally.
    Tests end-to-end synthesis, audio binary output, and WAV header integrity.
    """
    client = TestClient(tts_app)
    req = {
        "text": "Hello, this is a real local speech synthesis test from EchoMCP.",
        "voice_id": "1",
        "speed": 1.0,
        "format": "wav",
        "emotion": "happy"
    }

    res = client.post("/synthesize", json=req)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"

    # Verify audio metadata headers
    duration_str = res.headers.get("X-Audio-Duration")
    sample_rate_str = res.headers.get("X-Sample-Rate")
    channels_str = res.headers.get("X-Channels")

    assert duration_str is not None
    assert float(duration_str) > 0.0
    assert sample_rate_str == "22050"
    assert channels_str == "1"

    # Persist and inspect the real produced WAV file locally
    output_wav_file = tmp_path / "real_synthesized_output.wav"
    output_wav_file.write_bytes(res.content)
    assert output_wav_file.exists()
    assert output_wav_file.stat().st_size > 1000

    # Parse and validate real WAV RIFF header
    with wave.open(str(output_wav_file), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()

        assert channels == 1
        assert sampwidth == 2  # 16-bit PCM
        assert framerate == 22050
        assert nframes > 0

def test_tts_failure_handling_empty_text():
    """Verify synthesis failure handling on empty or whitespace text."""
    client = TestClient(tts_app)
    res = client.post("/synthesize", json={"text": "   ", "voice_id": "1"})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_tts_failure_handling_invalid_speed():
    """Verify input validation fails on out-of-range speed multiplier."""
    client = TestClient(tts_app)
    res = client.post("/synthesize", json={"text": "Valid text", "speed": 10.0})
    assert res.status_code in [400, 422]
