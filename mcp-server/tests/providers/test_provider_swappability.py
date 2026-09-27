import io
import wave
import pytest
from app.services.providers.base import TTSProvider
from app.services.providers.mock import MockTTSProvider
from app.services.speech_service import SpeechService
from app.models.speech import SpeechRequest, AudioFormat

class AlternativeTTSProvider(TTSProvider):
    """Simulates a lightweight alternative TTS engine (e.g. Kokoro / Piper)."""
    async def health(self) -> dict:
        return {"status": "ok", "engine": "alternative"}

    async def status(self) -> dict:
        return {"provider": "alternative", "status": "ready", "model_loaded": True}

    async def synthesize(
        self,
        text: str,
        voice_id: str = "1",
        speed: float = 1.0,
        format: str = "wav",
        emotion: str | None = None
    ) -> tuple[bytes, dict]:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(b"\x00\x00" * 24000)
        return buf.getvalue(), {
            "duration_seconds": 1.0,
            "sample_rate": 24000,
            "channels": 1,
            "format": format
        }

    async def register_voice(self, voice_id: str, name: str, file_path: str) -> dict:
        return {"voice_id": voice_id, "status": "ready"}

    async def delete_voice(self, voice_id: str) -> bool:
        return True

    async def list_voices(self) -> list[dict]:
        return [{"voice_id": "1", "name": "Alternative Voice 1", "status": "ready"}]

@pytest.mark.asyncio
async def test_speech_service_swappability_mock_and_alternative(test_audio_svc, test_voice_svc):
    """
    PASS Criteria Verification:
    Proves that SpeechService (and consequently MCP) works with multiple different
    TTS providers adhering to TTSProvider without knowing which provider is underneath.
    """
    providers: list[TTSProvider] = [
        MockTTSProvider(),
        AlternativeTTSProvider(),
    ]

    req = SpeechRequest(
        text="Testing swappable TTS provider architecture.",
        voice_id="1",
        speed=1.0,
        format=AudioFormat.WAV
    )

    for provider in providers:
        # Instantiate speech service with current provider
        service = SpeechService(
            tts_provider=provider,
            audio_service=test_audio_svc,
            voice_service=test_voice_svc
        )

        res, metrics = await service.speak(req)

        assert res.status.value == "completed"
        assert res.audio_id.startswith("aud_")
        assert res.duration_seconds > 0
        assert metrics.tts_latency_ms >= 0
        assert metrics.total_latency_ms > 0

        # Verify persisted file can be retrieved
        meta = test_audio_svc.get_audio_metadata(res.audio_id)
        assert meta is not None
        assert meta.text == "Testing swappable TTS provider architecture."
