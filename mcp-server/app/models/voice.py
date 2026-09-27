from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class VoiceStatus(str, Enum):
    READY = "ready"
    MISSING = "missing"
    PROCESSING = "processing"
    ERROR = "error"

class VoiceMetadata(BaseModel):
    voice_id: str = Field(default="1")
    name: str = Field(default="Voice 1")
    reference_file: str = Field(default="reference.wav")
    transcript: Optional[str] = None
    sample_rate: int = 22050
    channels: int = 1
    duration_seconds: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: VoiceStatus = VoiceStatus.READY

class TTSStatusResponse(BaseModel):
    provider: str
    status: str
    model_loaded: bool
