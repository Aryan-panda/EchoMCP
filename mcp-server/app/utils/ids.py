import re
import uuid

AUDIO_ID_PATTERN = re.compile(r"^aud_[a-zA-Z0-9_-]+$")

def generate_request_id() -> str:
    """Generate a unique request tracing ID."""
    return f"req_{uuid.uuid4().hex[:16]}"

def generate_audio_id() -> str:
    """Generate a persistent audio record ID."""
    return f"aud_{uuid.uuid4().hex[:16]}"

def is_valid_audio_id(audio_id: str) -> bool:
    """Validate that audio_id conforms to safe format and cannot contain path traversals."""
    return bool(AUDIO_ID_PATTERN.match(audio_id))
