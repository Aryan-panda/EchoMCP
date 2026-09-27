import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger("echomcp.cleanup")

def cleanup_expired_audio(output_dir: Path, retention_days: int) -> int:
    """Delete audio and metadata records older than retention_days."""
    if retention_days <= 0:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    metadata_dir = output_dir / "metadata"
    if not metadata_dir.exists():
        return 0

    deleted_count = 0
    for meta_file in metadata_dir.glob("aud_*.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            created_at_str = meta.get("created_at")
            if not created_at_str:
                continue

            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at < cutoff:
                # Remove audio file
                file_path_str = meta.get("file_path")
                if file_path_str:
                    audio_file = Path(file_path_str)
                    if not audio_file.is_absolute():
                        audio_file = output_dir.parent / file_path_str
                    if audio_file.exists():
                        audio_file.unlink()

                # Remove metadata file
                meta_file.unlink()
                deleted_count += 1
                logger.info(f"Cleaned up expired audio: {meta.get('audio_id')}")
        except Exception as e:
            logger.warning(f"Error checking audio file {meta_file}: {e}")

    return deleted_count
