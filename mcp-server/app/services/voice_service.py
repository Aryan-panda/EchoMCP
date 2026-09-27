import io
import json
import wave
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.voice import VoiceMetadata, VoiceStatus

logger = logging.getLogger("echomcp.voice_service")

class VoiceService:
    def __init__(self, voices_dir: Optional[Path] = None):
        self.voices_dir = Path(voices_dir or settings.voices_path).resolve()
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        (self.voices_dir / "1").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_reference_audio(audio_bytes: bytes) -> tuple[int, int, float]:
        """
        Validate audio bytes to ensure it is a valid, readable WAV file.
        Returns (sample_rate, channels, duration_seconds).
        Raises ValueError on corrupted or invalid audio.
        """
        if not audio_bytes or len(audio_bytes) < 44:
            raise ValueError("Reference audio file is empty or too small to contain a WAV header.")

        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                nframes = wf.getnframes()
                sampwidth = wf.getsampwidth()

                if channels not in [1, 2]:
                    raise ValueError(f"Unsupported channel count: {channels}. Must be Mono (1) or Stereo (2).")
                if sample_rate < 8000 or sample_rate > 48000:
                    raise ValueError(f"Unsupported sample rate: {sample_rate}Hz. Must be between 8000Hz and 48000Hz.")
                if nframes == 0:
                    raise ValueError("WAV file contains 0 audio frames.")

                duration = nframes / float(sample_rate)
                if duration < 0.5:
                    raise ValueError(f"Reference audio duration too short: {duration:.2f}s. Minimum required is 0.5s.")
                if duration > 120.0:
                    raise ValueError(f"Reference audio duration too long: {duration:.2f}s. Maximum allowed is 120s.")

                return sample_rate, channels, round(duration, 2)
        except wave.Error as e:
            raise ValueError(f"Invalid or corrupted WAV file: {str(e)}")

    def is_voice_ready(self, voice_id: str = "1") -> bool:
        """Check if target voice reference audio exists on disk."""
        target_dir = self.voices_dir / voice_id
        ref_file = target_dir / "reference.wav"
        return ref_file.exists() and ref_file.stat().st_size > 44

    def get_voice(self, voice_id: str = "1") -> Optional[VoiceMetadata]:
        target_dir = self.voices_dir / voice_id
        meta_file = target_dir / "metadata.json"
        ref_file = target_dir / "reference.wav"

        if not meta_file.exists() and not ref_file.exists():
            return None

        status = VoiceStatus.READY if (ref_file.exists() and ref_file.stat().st_size > 44) else VoiceStatus.MISSING

        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                data["status"] = status
                return VoiceMetadata(**data)
            except Exception as e:
                logger.error(f"Failed to read metadata for voice {voice_id}: {e}")

        # Fallback if only reference.wav exists
        sample_rate = 22050
        duration = 0.0
        channels = 1
        if ref_file.exists():
            try:
                sample_rate, channels, duration = self.validate_reference_audio(ref_file.read_bytes())
            except Exception:
                pass

        return VoiceMetadata(
            voice_id=voice_id,
            name=f"Voice {voice_id}",
            reference_file="reference.wav",
            sample_rate=sample_rate,
            channels=channels,
            duration_seconds=duration,
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
        """Validate and register a new reference audio sample."""
        # Step 1: Validate audio format
        sample_rate, channels, duration = self.validate_reference_audio(audio_bytes)

        target_dir = self.voices_dir / voice_id
        target_dir.mkdir(parents=True, exist_ok=True)

        ref_file = target_dir / "reference.wav"
        ref_file.write_bytes(audio_bytes)

        metadata = VoiceMetadata(
            voice_id=voice_id,
            name=name,
            reference_file="reference.wav",
            transcript=transcript,
            sample_rate=sample_rate,
            channels=channels,
            duration_seconds=duration,
            created_at=datetime.now(timezone.utc),
            status=VoiceStatus.READY
        )

        meta_file = target_dir / "metadata.json"
        meta_file.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Registered reference for voice {voice_id} ({name}): {duration}s, {sample_rate}Hz")
        return metadata

    def delete_voice(self, voice_id: str = "1") -> bool:
        """Remove configured reference voice without deleting generated audio history."""
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
