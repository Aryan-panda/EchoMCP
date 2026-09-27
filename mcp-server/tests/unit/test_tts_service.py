import io
import wave
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

tts_app_path = Path(__file__).resolve().parents[3] / "tts" / "app.py"
spec = importlib.util.spec_from_file_location("tts_service_app", str(tts_app_path))
tts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts_module)

tts_app = tts_module.app
generate_mock_wav = tts_module.generate_mock_wav

def test_generate_mock_wav_valid_audio():
    wav_bytes = generate_mock_wav(duration_seconds=1.0, sample_rate=22050)
    assert len(wav_bytes) > 0
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        assert wf.getnframes() == 22050

def test_tts_health_and_status():
    client = TestClient(tts_app)
    h_res = client.get("/health")
    assert h_res.status_code == 200
    assert h_res.json() == {"status": "ok"}

    s_res = client.get("/status")
    assert s_res.status_code == 200
    assert s_res.json()["status"] == "ready"

def test_tts_synthesize_endpoint():
    client = TestClient(tts_app)
    req = {
        "text": "Hello world from EchoMCP",
        "voice_id": "1",
        "speed": 1.0,
        "format": "wav"
    }
    res = client.post("/synthesize", json=req)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert "X-Audio-Duration" in res.headers
    assert len(res.content) > 1000
