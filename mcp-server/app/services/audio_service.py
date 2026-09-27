import os
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.audio import AudioMetadata, AudioSummaryItem, PaginatedAudioResponse
from app.models.speech import AudioFormat
from app.utils.ids import is_valid_audio_id

logger = logging.getLogger("echomcp.audio_service")

class AudioService:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir or settings.output_path).resolve()
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

    def list_audio(
        self,
        page: int = 1,
        limit: int = 20,
        voice_id: Optional[str] = None
    ) -> PaginatedAudioResponse:
        """List stored audio records with pagination, newest first."""
        records: list[AudioMetadata] = []
        if self.metadata_dir.exists():
            for meta_file in sorted(self.metadata_dir.glob("aud_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    record = AudioMetadata(**data)
                    if voice_id and record.voice_id != voice_id:
                        continue
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping malformed metadata {meta_file}: {e}")

        # Ensure sorted newest created_at first
        records.sort(key=lambda r: r.created_at, reverse=True)

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
                status=r.status,
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
                # Clean up parent directory if empty
                parent_dir = audio_path.parent
                if parent_dir != self.output_dir and not any(parent_dir.iterdir()):
                    try:
                        parent_dir.rmdir()
                    except OSError:
                        pass

        meta_file.unlink()
        logger.info(f"Deleted audio record {audio_id}")
        return True

    def cleanup_old_records(self, retention_days: Optional[int] = None) -> int:
        """
        Delete audio files and metadata older than retention_days.
        If retention_days is None, uses settings.AUDIO_RETENTION_DAYS.
        Cleans up empty dated directories afterwards.
        Returns count of removed records.
        """
        days = retention_days if retention_days is not None else settings.AUDIO_RETENTION_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_count = 0

        if not self.metadata_dir.exists():
            return 0

        for meta_file in list(self.metadata_dir.glob("aud_*.json")):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                created_at_str = data.get("created_at")
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str)
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                else:
                    created_at = datetime.fromtimestamp(meta_file.stat().st_mtime, tz=timezone.utc)

                if created_at < cutoff:
                    audio_id = data.get("audio_id", meta_file.stem)
                    if self.delete_audio(audio_id):
                        deleted_count += 1
            except Exception as e:
                logger.warning(f"Error during retention evaluation of {meta_file}: {e}")

        # Prune empty date directories
        self._prune_empty_dirs()
        logger.info(f"Retention cleanup finished: {deleted_count} records purged (retention: {days} days)")
        return deleted_count

    def _prune_empty_dirs(self):
        """Recursively remove empty date directories in output_dir, preserving metadata dir."""
        for root, dirs, files in os.walk(str(self.output_dir), topdown=False):
            root_path = Path(root)
            if root_path == self.output_dir or root_path == self.metadata_dir:
                continue
            try:
                if not any(root_path.iterdir()):
                    root_path.rmdir()
            except OSError:
                pass

