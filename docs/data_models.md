# EchoMCP — Domain Data Models & Schemas
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Phase 0 (Architecture & Contracts)  
**Implementation Framework:** Python 3.12+ / Pydantic v2  

---

## 1. Core Enumerations

```python
from enum import Enum

class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"

class VoiceStatus(str, Enum):
    READY = "ready"
    MISSING = "missing"
    PROCESSING = "processing"
    ERROR = "error"

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
```

---

## 2. Voice Domain Models

### 2.1 Voice Metadata (`tts/voices/1/metadata.json`)
```python
from datetime import datetime
from pydantic import BaseModel, Field

class VoiceMetadata(BaseModel):
    voice_id: str = Field(default="1", description="Unique voice identifier")
    name: str = Field(default="Voice 1", description="Human-readable voice display name")
    reference_file: str = Field(default="reference.wav", description="Relative filename of reference audio")
    transcript: str | None = Field(default=None, description="Optional ground-truth transcript of reference")
    sample_rate: int = Field(default=22050, description="Audio sample rate of reference in Hz")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    status: VoiceStatus = Field(default=VoiceStatus.READY, description="Readiness status")
```

---

## 3. Audio Domain Models

### 3.1 Audio Record Metadata (`tts/output/metadata/aud_<id>.json`)
```python
from datetime import datetime
from pydantic import BaseModel, Field

class AudioMetadata(BaseModel):
    audio_id: str = Field(..., description="Unique audio identifier prefixed with aud_")
    text: str = Field(..., description="Clean spoken text without control tags")
    voice_id: str = Field(default="1", description="Voice profile ID used for synthesis")
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Audio container format")
    duration_seconds: float = Field(..., ge=0.0, description="Duration of generated audio in seconds")
    sample_rate: int = Field(..., ge=8000, le=48000, description="Sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels (1 = Mono)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    file_path: str = Field(..., description="Relative path to audio file on disk")
    file_size_bytes: int = Field(..., ge=0, description="Size of file on disk in bytes")
```

### 3.2 Paginated Audio Response
```python
from pydantic import BaseModel, Field

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
    total: int = Field(..., ge=0, description="Total count of stored audio records")
    page: int = Field(..., ge=1, description="Current page index")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    items: list[AudioSummaryItem] = Field(default_factory=list, description="List of audio items")
```

---

## 4. Emotion & Prosody Models

### 4.1 Segment Representation
```python
from pydantic import BaseModel, Field

class EmotionSegment(BaseModel):
    text: str = Field(..., min_length=1, description="Clean textual segment to synthesize")
    emotion: SupportedEmotion = Field(default=SupportedEmotion.NEUTRAL, description="Target emotion tag")
    pause_ms: int = Field(default=0, ge=0, description="Inter-segment silence duration in ms")

class ParsedSpeech(BaseModel):
    raw_text: str = Field(..., description="Original raw input string containing control tags")
    clean_text: str = Field(..., description="Normalized full text with all tags cleanly removed")
    segments: list[EmotionSegment] = Field(..., description="Ordered list of emotion-attributed segments")
```

---

## 5. Speech Synthesis Requests & Responses

### 5.1 REST Speech Request & Response
```python
from datetime import datetime
from pydantic import BaseModel, Field

class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text with optional tags")
    voice_id: str = Field(default="1", description="Target voice profile ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Playback speed multiplier")
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Target format")

class SpeechResponse(BaseModel):
    audio_id: str = Field(..., description="Generated audio identifier")
    status: SynthesisStatus = Field(default=SynthesisStatus.COMPLETED)
    duration_seconds: float = Field(..., ge=0.0)
    format: AudioFormat = Field(default=AudioFormat.WAV)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    audio_url: str = Field(...)
```

---

## 6. MCP Protocol Models

### 6.1 `speak_response` Tool Input & Structured Output
```python
from pydantic import BaseModel, Field

class MCPSpeakToolInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Response text to synthesize")
    voice_id: str = Field(default="1", description="Target voice ID (defaults to '1')")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech rate multiplier")
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Output format (wav or mp3)")

class MCPSpeakToolOutput(BaseModel):
    audio_id: str
    status: str = "completed"
    format: str
    duration_seconds: float
    audio_url: str
```

---

## 7. Observability & Latency Models

```python
from pydantic import BaseModel, Field

class LatencyMetrics(BaseModel):
    mcp_overhead_ms: float = Field(..., ge=0.0, description="Time spent in validation and dispatch")
    tts_latency_ms: float = Field(..., ge=0.0, description="Time spent in TTS synthesis")
    storage_latency_ms: float = Field(..., ge=0.0, description="Time spent persisting WAV and JSON to disk")
    total_latency_ms: float = Field(..., ge=0.0, description="Total wall-clock duration from ingress to egress")

class StructuredLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(...)
    operation: str = Field(...)
    voice_id: str = Field(...)
    text_length: int = Field(..., ge=0)
    tts_provider: str = Field(...)
    metrics: LatencyMetrics = Field(...)
    status: str = Field(...)
    error: str | None = None
```

---

## 8. System Status & Readiness Models

```python
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "ok"

class ReadinessResponse(BaseModel):
    mcp: bool = Field(..., description="MCP server initialization status")
    tts: bool = Field(..., description="TTS backend connectivity status")
    voice_1: bool = Field(..., description="Voice ID 1 reference file readiness")
    audio_store: bool = Field(..., description="Filesystem audio storage writeability")
    ready: bool = Field(..., description="Overall system readiness flag")

class VersionResponse(BaseModel):
    name: str = "grok-voice-bridge"
    version: str = "1.0.0"

class TTSStatusResponse(BaseModel):
    provider: str = Field(..., description="Active TTS provider name")
    status: str = Field(..., description="ready | unavailable | error")
    model_loaded: bool = Field(...)
```

---

## 9. Typed Error Hierarchy

```python
class EchoMCPError(Exception):
    """Base exception for all domain errors in EchoMCP."""
    status_code: int = 500
    code: str = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class InvalidTextError(EchoMCPError):
    status_code = 400
    code = "INVALID_TEXT_ERROR"

class InvalidFormatError(EchoMCPError):
    status_code = 400
    code = "INVALID_FORMAT_ERROR"

class RequestTooLargeError(EchoMCPError):
    status_code = 400
    code = "REQUEST_TOO_LARGE_ERROR"

class AuthenticationError(EchoMCPError):
    status_code = 401
    code = "AUTHENTICATION_ERROR"

class VoiceNotFoundError(EchoMCPError):
    status_code = 404
    code = "VOICE_NOT_FOUND_ERROR"

class AudioNotFoundError(EchoMCPError):
    status_code = 404
    code = "AUDIO_NOT_FOUND_ERROR"

class TTSUnavailableError(EchoMCPError):
    status_code = 503
    code = "TTS_UNAVAILABLE_ERROR"

class TTSGenerationError(EchoMCPError):
    status_code = 502
    code = "TTS_GENERATION_ERROR"

class AudioStorageError(EchoMCPError):
    status_code = 500
    code = "AUDIO_STORAGE_ERROR"
```
