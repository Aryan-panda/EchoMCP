from abc import ABC, abstractmethod
from typing import Optional

class TTSProvider(ABC):
    """Abstract interface for speech synthesis engines."""

    @abstractmethod
    async def health(self) -> dict:
        """Check provider health status."""
        pass

    @abstractmethod
    async def status(self) -> dict:
        """Query engine and model status."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str = "1",
        speed: float = 1.0,
        format: str = "wav",
        emotion: Optional[str] = None
    ) -> tuple[bytes, dict]:
        """Synthesize text and return (audio_bytes, audio_metadata_dict)."""
        pass

    @abstractmethod
    async def register_voice(self, voice_id: str, name: str, file_path: str) -> dict:
        """Register or update a voice profile."""
        pass

    @abstractmethod
    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a registered voice profile."""
        pass
