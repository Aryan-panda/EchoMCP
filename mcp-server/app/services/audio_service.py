import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.audio import AudioMetadata, AudioSummaryItem, PaginatedAudioResponse
from app.models.speech import AudioFormat
from app.utils.ids import is_valid_audio_id

logger = logging.getLogger("echomcp.audio_service")

class AudioService:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.output_path
        self.metadata_dir = self.output_dir / "metadata"
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_audio(
        self,
        audio_id: str,
        text: str,
        audio_bytes: bytes,
        voice_id: str = "1",
        audio_format: AudioFormat = AudioFormat.WAV,
        duration_seconds: float = 2.0,
        sample_rate: int = 22050,
        channels: int = 1,
    ) -> AudioMetadata:
        """Save generated audio and its companion metadata to persistent storage."""
        now = datetime.now(timezone.utc)
        # Partition directory by YYYY/MM/DD
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")
        day_str = now.strftime("%d")

        rel_dir = Path(year_str) / month_str / day_str
        target_dir = self.output_dir / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{audio_id}.{audio_format.value}"
        file_path = target_dir / filename
        rel_file_path = f"{rel_dir}/{filename}".replace("\\", "/")

        # Write audio binary
        file_path.write_bytes(audio_bytes)
        file_size = len(audio_bytes)

        metadata = AudioMetadata(
            audio_id=audio_id,
            text=text,
            voice_id=voice_id,
            format=audio_format,
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            channels=channels,
            created_at=now,
            file_path=rel_file_path,
            file_size_bytes=file_size,
        )

        # Write metadata JSON
        meta_file = self.metadata_dir / f"{audio_id}.json"
        meta_file.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

        logger.info(f"Persisted audio {audio_id} ({duration_seconds}s, {file_size} bytes)")
        return metadata

    def get_audio_metadata(self, audio_id: str) -> Optional[AudioMetadata]:
        """Fetch metadata for a specific audio record."""
        if not is_valid_audio_id(audio_id):
            return None

        meta_file = self.metadata_dir / f"{audio_id}.json"
        if not meta_file.exists():
            return None

        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            return AudioMetadata(**data)
        except Exception as e:
            logger.error(f"Failed to read metadata for {audio_id}: {e}")
            return None

    def get_audio_file_path(self, audio_id: str) -> Optional[Path]:
        """Retrieve absolute file path for audio streaming."""
        meta = self.get_audio_metadata(audio_id)
        if not meta:
            return None

        full_path = self.output_dir / meta.file_path
        if full_path.exists():
            return full_path
        return None

    def list_audio(self, page: int = 1, limit: int = 20) -> PaginatedAudioResponse:
        """List stored audio records with pagination, newest first."""
        records: list[AudioMetadata] = []
        if self.metadata_dir.exists():
            for meta_file in sorted(self.metadata_dir.glob("aud_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    records.append(AudioMetadata(**data))
                except Exception as e:
                    logger.warning(f"Skipping malformed metadata {meta_file}: {e}")

        total = len(records)
        start = (page - 1) * limit
        end = start + limit
        page_items = records[start:end]

        summary_items = [
            AudioSummaryItem(
                audio_id=r.audio_id,
                text=r.text,
                voice_id=r.voice_id,
                format=r.format,
                duration_seconds=r.duration_seconds,
                sample_rate=r.sample_rate,
                channels=r.channels,
                created_at=r.created_at,
                audio_url=f"/api/v1/audio/{r.audio_id}",
                file_url=f"/api/v1/audio/{r.audio_id}/file",
            )
            for r in page_items
        ]

        return PaginatedAudioResponse(
            total=total,
            page=page,
            limit=limit,
            items=summary_items
        )

    def delete_audio(self, audio_id: str) -> bool:
        """Delete audio file and metadata record from disk."""
        if not is_valid_audio_id(audio_id):
            return False

        meta_file = self.metadata_dir / f"{audio_id}.json"
        if not meta_file.exists():
            return False

        meta = self.get_audio_metadata(audio_id)
        if meta:
            audio_path = self.output_dir / meta.file_path
            if audio_path.exists():
                audio_path.unlink()

        meta_file.unlink()
        logger.info(f"Deleted audio record {audio_id}")
        return True
