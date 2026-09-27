import io
import wave
import pytest
from app.services.providers.mock import MockTTSProvider

@pytest.mark.asyncio
async def test_mock_provider_health_and_status():
    provider = MockTTSProvider()
    h = await provider.health()
    assert h == {"status": "ok"}

    s = await provider.status()
    assert s["provider"] == "mock"
    assert s["status"] == "ready"
    assert s["model_loaded"] is True

@pytest.mark.asyncio
async def test_mock_provider_synthesize():
    provider = MockTTSProvider(sample_rate=22050)
    audio_bytes, meta = await provider.synthesize(
        text="Testing mock synthesis output duration and audio data.",
        voice_id="1",
        speed=1.0,
        format="wav"
    )

    assert len(audio_bytes) > 0
    assert meta["format"] == "wav"
    assert meta["sample_rate"] == 22050
    assert meta["channels"] == 1
    assert meta["duration_seconds"] > 0

    with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        assert wf.getnframes() > 0

@pytest.mark.asyncio
async def test_mock_provider_voice_lifecycle():
    provider = MockTTSProvider()
    
    # Initial voices
    initial = await provider.list_voices()
    assert any(v["voice_id"] == "1" for v in initial)

    # Register voice 2
    reg = await provider.register_voice("2", "Test Voice 2", "dummy.wav")
    assert reg["voice_id"] == "2"

    voices_after = await provider.list_voices()
    assert len(voices_after) == 2

    # Delete voice 2
    del_ok = await provider.delete_voice("2")
    assert del_ok is True

    voices_final = await provider.list_voices()
    assert len(voices_final) == 1
