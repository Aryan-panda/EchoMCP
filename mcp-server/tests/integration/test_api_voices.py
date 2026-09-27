import io
import wave
import struct
import pytest

def generate_valid_test_wav(duration: float = 2.0, sample_rate: int = 22050) -> bytes:
    """Generate in-memory valid WAV bytes for testing upload and validation."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        nframes = int(duration * sample_rate)
        frames = bytearray()
        for i in range(nframes):
            frames.extend(struct.pack("<h", 1000))
        wf.writeframes(frames)
    return buf.getvalue()

def test_list_voices_endpoint(client):
    """Verify listing voices returns Voice 1."""
    res = client.get("/api/v1/voices")
    assert res.status_code == 200
    voices = res.json()
    assert isinstance(voices, list)
    assert len(voices) >= 1
    v1 = next((v for v in voices if v["voice_id"] == "1"), None)
    assert v1 is not None
    assert v1["status"] in ["ready", "missing"]

def test_upload_valid_voice_reference(client):
    """Verify registering a valid WAV reference for Voice ID 1."""
    wav_bytes = generate_valid_test_wav(duration=2.0, sample_rate=22050)
    files = {"file": ("my_voice.wav", wav_bytes, "audio/wav")}
    data = {
        "voice_id": "1",
        "name": "Custom Voice 1",
        "transcript": "Testing voice reference upload."
    }

    res = client.post("/api/v1/voices", files=files, data=data)
    assert res.status_code == 201
    meta = res.json()
    assert meta["voice_id"] == "1"
    assert meta["name"] == "Custom Voice 1"
    assert meta["status"] == "ready"
    assert meta["duration_seconds"] == 2.0
    assert meta["sample_rate"] == 22050

def test_upload_invalid_non_wav_file(client):
    """Verify rejection of non-WAV / corrupted audio."""
    fake_bytes = b"This is not a valid WAV file content at all. Padding to make it longer than 44 bytes header size."
    files = {"file": ("corrupt.wav", fake_bytes, "audio/wav")}
    data = {"voice_id": "1", "name": "Bad Voice"}

    res = client.post("/api/v1/voices", files=files, data=data)
    assert res.status_code == 400
    assert any(term in res.json()["detail"].lower() for term in ["invalid", "corrupt", "wav"])

def test_upload_audio_too_short(client):
    """Verify rejection of audio shorter than minimum duration."""
    short_wav = generate_valid_test_wav(duration=0.1, sample_rate=22050)
    files = {"file": ("short.wav", short_wav, "audio/wav")}
    data = {"voice_id": "1", "name": "Too Short"}

    res = client.post("/api/v1/voices", files=files, data=data)
    assert res.status_code == 400
    assert "too short" in res.json()["detail"].lower()

def test_upload_rejects_non_voice_id_1(client):
    """Verify rejection of arbitrary voice IDs in V1."""
    wav_bytes = generate_valid_test_wav(duration=1.5)
    files = {"file": ("voice.wav", wav_bytes, "audio/wav")}
    data = {"voice_id": "99", "name": "Voice 99"}

    res = client.post("/api/v1/voices", files=files, data=data)
    assert res.status_code == 400
    assert "only supports" in res.json()["detail"].lower()

def test_voice_synthesis_and_audio_playback(client):
    """
    PASS CRITERIA:
    Voice ID 1 produces speech using the reference voice and allows audio playback.
    """
    # 1. Synthesize speech using Voice 1
    speak_req = {
        "text": "Hello, testing speech generated using configured Voice ID 1.",
        "voice_id": "1",
        "speed": 1.0,
        "format": "wav"
    }
    speak_res = client.post("/api/v1/speak", json=speak_req)
    assert speak_res.status_code == 200
    audio_data = speak_res.json()
    audio_id = audio_data["audio_id"]
    assert audio_id.startswith("aud_")

    # 2. Test Audio Playback endpoint
    file_res = client.get(f"/api/v1/audio/{audio_id}/file")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"] == "audio/wav"
    assert file_res.headers["accept-ranges"] == "bytes"
    assert len(file_res.content) > 1000

    # 3. Verify WAV integrity of generated playback audio
    with wave.open(io.BytesIO(file_res.content), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        assert wf.getnframes() > 0

def test_delete_voice_1_safety(client):
    """Verify deleting Voice 1 does not delete generated audio files."""
    # Ensure Voice 1 reference is uploaded first
    wav_bytes = generate_valid_test_wav(duration=1.0)
    client.post("/api/v1/voices", files={"file": ("v.wav", wav_bytes, "audio/wav")}, data={"voice_id": "1"})

    # Generate an audio file with Voice 1
    s_res = client.post("/api/v1/speak", json={"text": "Audio before voice deletion.", "voice_id": "1"})
    audio_id = s_res.json()["audio_id"]

    # Delete Voice 1
    del_res = client.delete("/api/v1/voices/1")
    assert del_res.status_code == 204

    # Verify voice status is now missing
    voices = client.get("/api/v1/voices").json()
    v1 = next((v for v in voices if v["voice_id"] == "1"), None)
    assert v1["status"] == "missing"

    # Crucial Invariant: The previously generated audio MUST still exist and be playable!
    play_res = client.get(f"/api/v1/audio/{audio_id}/file")
    assert play_res.status_code == 200
    assert len(play_res.content) > 0
