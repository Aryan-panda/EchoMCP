import io
import math
import struct
import wave
from typing import Optional
from .base import TTSProvider

class MockTTSProvider(TTSProvider):
    """In-memory mock TTS provider for testing without a downstream container."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.registered_voices = {"1": "Voice 1"}

    async def health(self) -> dict:
        return {"status": "ok"}

    async def status(self) -> dict:
        return {"provider": "mock", "status": "ready", "model_loaded": True}

    async def synthesize(
        self,
        text: str,
        voice_id: str = "1",
        speed: float = 1.0,
        format: str = "wav",
        emotion: Optional[str] = None
    ) -> tuple[bytes, dict]:
        words = len(text.split())
        duration = max(1.0, min(10.0, (words / 3.0) / speed))
        num_samples = int(duration * self.sample_rate)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            frames = bytearray()
            for i in range(num_samples):
                val = int(4000.0 * math.sin(2.0 * math.pi * 440.0 * (i / self.sample_rate)))
                frames.extend(struct.pack("<h", max(-32768, min(32767, val))))
            wf.writeframes(frames)

        meta = {
            "duration_seconds": round(duration, 2),
            "sample_rate": self.sample_rate,
            "channels": 1,
            "format": format
        }
        return buf.getvalue(), meta

    async def register_voice(self, voice_id: str, name: str, file_path: str) -> dict:
        self.registered_voices[voice_id] = name
        return {"voice_id": voice_id, "name": name, "status": "ready"}

    async def delete_voice(self, voice_id: str) -> bool:
        if voice_id in self.registered_voices:
            del self.registered_voices[voice_id]
            return True
        return False

    async def list_voices(self) -> list[dict]:
        return [
            {"voice_id": vid, "name": name, "status": "ready"}
            for vid, name in self.registered_voices.items()
        ]
