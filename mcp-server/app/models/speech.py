from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"

class SupportedEmotion(str, Enum):
    HAPPY = "happy"
    AMUSED = "amused"
    EXCITED = "excited"
    SAD = "sad"
    ANGRY = "angry"
    WHISPER = "whisper"
    LAUGHING = "laughing"
    PAUSE = "pause"
    NEUTRAL = "neutral"

class SynthesisStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"

class EmotionSegment(BaseModel):
    text: str = Field(..., min_length=1)
    emotion: SupportedEmotion = Field(default=SupportedEmotion.NEUTRAL)
    pause_ms: int = Field(default=0, ge=0)

class ParsedSpeech(BaseModel):
    raw_text: str
    clean_text: str
    segments: list[EmotionSegment]

class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(default="1")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    format: AudioFormat = Field(default=AudioFormat.WAV)

class SpeechResponse(BaseModel):
    audio_id: str
    status: SynthesisStatus = Field(default=SynthesisStatus.COMPLETED)
    duration_seconds: float = Field(..., ge=0.0)
    format: AudioFormat = Field(default=AudioFormat.WAV)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audio_url: str

class MCPSpeakToolInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(default="1")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    format: AudioFormat = Field(default=AudioFormat.WAV)

class MCPSpeakToolOutput(BaseModel):
    audio_id: str
    status: str = "completed"
    format: str
    duration_seconds: float
    audio_url: str

class LatencyMetrics(BaseModel):
    mcp_overhead_ms: float = Field(..., ge=0.0)
    tts_latency_ms: float = Field(..., ge=0.0)
    storage_latency_ms: float = Field(..., ge=0.0)
    total_latency_ms: float = Field(..., ge=0.0)
