from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.speech import AudioFormat

class AudioMetadata(BaseModel):
    audio_id: str
    text: str
    voice_id: str = "1"
    format: AudioFormat = AudioFormat.WAV
    duration_seconds: float
    sample_rate: int = 22050
    channels: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_path: str
    file_size_bytes: int = 0

class AudioSummaryItem(BaseModel):
    audio_id: str
    text: str
    voice_id: str
    format: AudioFormat
    duration_seconds: float
    sample_rate: int
    channels: int
    created_at: datetime
    audio_url: str
    file_url: str

class PaginatedAudioResponse(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    items: list[AudioSummaryItem] = Field(default_factory=list)
