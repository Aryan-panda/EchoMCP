import io
import wave
import pytest
import httpx
from app.services.providers.cosyvoice import CosyVoiceProvider

def create_sample_wav():
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00\x00" * 22050)
    return buf.getvalue()

def mock_transport_handler(request: httpx.Request) -> httpx.Response:
    url = str(request.url)

    if url.endswith("/health"):
        return httpx.Response(200, json={"status": "ok"})

    elif url.endswith("/status"):
        return httpx.Response(200, json={"provider": "cosyvoice", "status": "ready", "model_loaded": True})

    elif url.endswith("/synthesize"):
        sample_wav = create_sample_wav()
        headers = {
            "Content-Type": "audio/wav",
            "X-Audio-Duration": "3.5",
            "X-Sample-Rate": "22050",
            "X-Channels": "1"
        }
        return httpx.Response(200, content=sample_wav, headers=headers)

    elif "/voices/register" in url:
        return httpx.Response(200, json={"voice_id": "1", "name": "Voice 1", "status": "ready"})

    elif url.endswith("/voices/1"):
        return httpx.Response(200, json={"status": "deleted"})

    elif url.endswith("/voices"):
        return httpx.Response(200, json=[{"voice_id": "1", "name": "Voice 1", "status": "ready"}])

    return httpx.Response(404)

@pytest.fixture
def mock_cosy_provider(monkeypatch):
    provider = CosyVoiceProvider(base_url="http://mock-tts:8080")
    # Patch httpx.AsyncClient to use our in-memory MockTransport
    transport = httpx.MockTransport(mock_transport_handler)
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: orig_client(transport=transport, **kwargs))
    return provider

@pytest.mark.asyncio
async def test_cosyvoice_health_and_status(mock_cosy_provider):
    h = await mock_cosy_provider.health()
    assert h == {"status": "ok"}

    s = await mock_cosy_provider.status()
    assert s["provider"] == "cosyvoice"
    assert s["status"] == "ready"
    assert s["model_loaded"] is True

@pytest.mark.asyncio
async def test_cosyvoice_synthesize(mock_cosy_provider):
    audio_bytes, meta = await mock_cosy_provider.synthesize(
        text="Hello world from CosyVoice provider test",
        voice_id="1",
        speed=1.0,
        format="wav"
    )

    assert len(audio_bytes) > 0
    assert meta["duration_seconds"] == 3.5
    assert meta["sample_rate"] == 22050
    assert meta["channels"] == 1
    assert meta["format"] == "wav"

@pytest.mark.asyncio
async def test_cosyvoice_voice_lifecycle(mock_cosy_provider):
    reg = await mock_cosy_provider.register_voice("1", "Voice 1", "reference.wav")
    assert reg["status"] == "ready"

    voices = await mock_cosy_provider.list_voices()
    assert len(voices) >= 1

    del_ok = await mock_cosy_provider.delete_voice("1")
    assert del_ok is True
