import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.voice import VoiceMetadata, VoiceStatus

logger = logging.getLogger("echomcp.voice_service")

class VoiceService:
    def __init__(self, voices_dir: Optional[Path] = None):
        self.voices_dir = voices_dir or settings.voices_path
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        (self.voices_dir / "1").mkdir(parents=True, exist_ok=True)

    def is_voice_ready(self, voice_id: str = "1") -> bool:
        """Check if target voice reference audio exists on disk."""
        target_dir = self.voices_dir / voice_id
        ref_file = target_dir / "reference.wav"
        return ref_file.exists() and ref_file.stat().st_size > 0

    def get_voice(self, voice_id: str = "1") -> Optional[VoiceMetadata]:
        target_dir = self.voices_dir / voice_id
        meta_file = target_dir / "metadata.json"
        ref_file = target_dir / "reference.wav"

        if not meta_file.exists() and not ref_file.exists():
            return None

        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                status = VoiceStatus.READY if ref_file.exists() else VoiceStatus.MISSING
                data["status"] = status
                return VoiceMetadata(**data)
            except Exception as e:
                logger.error(f"Failed to read metadata for voice {voice_id}: {e}")

        # Fallback if only reference.wav exists
        status = VoiceStatus.READY if ref_file.exists() else VoiceStatus.MISSING
        return VoiceMetadata(
            voice_id=voice_id,
            name=f"Voice {voice_id}",
            reference_file="reference.wav",
            status=status
        )

    def list_voices(self) -> list[VoiceMetadata]:
        v1 = self.get_voice("1")
        if v1:
            return [v1]
        return [
            VoiceMetadata(
                voice_id="1",
                name="Voice 1",
                status=VoiceStatus.MISSING
            )
        ]

    def register_voice_reference(
        self,
        voice_id: str,
        name: str,
        audio_bytes: bytes,
        transcript: Optional[str] = None
    ) -> VoiceMetadata:
        target_dir = self.voices_dir / voice_id
        target_dir.mkdir(parents=True, exist_ok=True)

        ref_file = target_dir / "reference.wav"
        ref_file.write_bytes(audio_bytes)

        metadata = VoiceMetadata(
            voice_id=voice_id,
            name=name,
            reference_file="reference.wav",
            transcript=transcript,
            created_at=datetime.now(timezone.utc),
            status=VoiceStatus.READY
        )

        meta_file = target_dir / "metadata.json"
        meta_file.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Registered reference for voice {voice_id} ({name})")
        return metadata

    def delete_voice(self, voice_id: str = "1") -> bool:
        target_dir = self.voices_dir / voice_id
        ref_file = target_dir / "reference.wav"
        meta_file = target_dir / "metadata.json"

        deleted = False
        if ref_file.exists():
            ref_file.unlink()
            deleted = True
        if meta_file.exists():
            meta_file.unlink()
            deleted = True

        logger.info(f"Deleted voice profile {voice_id}")
        return deleted
