import logging
from typing import Optional
import httpx
from app.config import settings
from .base import TTSProvider

logger = logging.getLogger("echomcp.cosyvoice_provider")

class CosyVoiceProvider(TTSProvider):
    """TTS provider communicating with internal TTS HTTP service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.TTS_BASE_URL).rstrip("/")

    async def health(self) -> dict:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()

    async def status(self) -> dict:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{self.base_url}/status")
            resp.raise_for_status()
            return resp.json()

    async def synthesize(
        self,
        text: str,
        voice_id: str = "1",
        speed: float = 1.0,
        format: str = "wav",
        emotion: Optional[str] = None
    ) -> tuple[bytes, dict]:
        payload = {
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "format": format,
            "emotion": emotion
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/synthesize", json=payload)
            resp.raise_for_status()
            
            duration = float(resp.headers.get("X-Audio-Duration", "2.0"))
            sample_rate = int(resp.headers.get("X-Sample-Rate", "22050"))
            channels = int(resp.headers.get("X-Channels", "1"))
            
            meta = {
                "duration_seconds": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "format": format
            }
            return resp.content, meta

    async def register_voice(self, voice_id: str, name: str, file_path: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/voices/register",
                params={"voice_id": voice_id, "name": name}
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_voice(self, voice_id: str) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.delete(f"{self.base_url}/voices/{voice_id}")
            return resp.status_code == 200

    async def list_voices(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/voices")
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                logger.warning(f"Error fetching voices from TTS service: {e}")
            return [{"voice_id": "1", "name": "Voice 1", "status": "ready"}]
