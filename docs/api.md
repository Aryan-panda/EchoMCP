# EchoMCP — REST API Specification
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Phase 0 (Architecture & Contracts)  
**Base URL:** `http://localhost:3001`  

---

## 1. Overview & Conventions

The EchoMCP REST API provides endpoints for:
1. System diagnostics and container readiness probes.
2. Speech synthesis orchestration (used internally by MCP and locally by the Web Dashboard).
3. Paginated audio history and binary audio playback streaming.
4. Reference voice profile management (Voice ID 1).
5. TTS engine status monitoring.

### Standard Request & Response Formats
- Content-Type: `application/json` for standard requests and responses.
- Binary Audio: `audio/wav` or `audio/mpeg` with `Accept-Ranges: bytes` support.
- Multipart: `multipart/form-data` for voice reference uploads.

### Standard Error Response Format
All error responses adhere to the RFC 7807 Problem Details inspired schema:
```json
{
  "error": {
    "code": "INVALID_TEXT_ERROR",
    "message": "The supplied text exceeds the maximum allowed length of 5000 characters.",
    "request_id": "req_01J8XK9R2Q0000000000000001",
    "details": {
      "field": "text",
      "max_length": 5000,
      "received_length": 5820
    }
  }
}
```

---

## 2. System Endpoints

### 2.1 Health Check (Liveness Probe)
Verifies that the MCP server process is running and accepting HTTP connections.

- **Method:** `GET`
- **Path:** `/health`
- **Authentication:** None (Public)
- **Response:** `200 OK`
```json
{
  "status": "ok"
}
```

---

### 2.2 Readiness Check (Readiness Probe)
Performs deep dependency checks on the MCP server, TTS downstream connectivity, Voice ID 1 registration, and audio filesystem writeability.

- **Method:** `GET`
- **Path:** `/ready`
- **Authentication:** None (Internal / Container Healthcheck)
- **Response Status:**
  - `200 OK` if all subsystems are operational (`ready: true`).
  - `503 Service Unavailable` if one or more essential components are unready (`ready: false`).
```json
{
  "mcp": true,
  "tts": true,
  "voice_1": true,
  "audio_store": true,
  "ready": true
}
```

---

### 2.3 Version Information
Returns system name, semantic version, and runtime environment.

- **Method:** `GET`
- **Path:** `/version`
- **Authentication:** None
- **Response:** `200 OK`
```json
{
  "name": "grok-voice-bridge",
  "version": "1.0.0"
}
```

---

## 3. Speech Endpoints

### 3.1 Direct Speech Synthesis
Direct HTTP entry point to synthesize speech with emotion tags and persist the resulting audio to disk.

- **Method:** `POST`
- **Path:** `/api/v1/speak`
- **Authentication:** Bearer Token (`Authorization: Bearer <MCP_AUTH_TOKEN>`)
- **Headers:**
  - `Content-Type: application/json`

#### Request Payload
```json
{
  "text": "[amused] Oh, come on. Did you really think that would work? [laughing] That's wild.",
  "voice_id": "1",
  "speed": 1.0,
  "format": "wav"
}
```

| Field | Type | Required | Default | Validation Rules |
| :--- | :--- | :--- | :--- | :--- |
| `text` | string | Yes | — | Min 1 char, max 5000 chars. Non-empty after strip. |
| `voice_id` | string | No | `"1"` | Must correspond to registered voice (`"1"` for V1). |
| `speed` | float | No | `1.0` | Value must be between `0.5` and `2.0`. |
| `format` | string | No | `"wav"` | Allowed values: `"wav"`, `"mp3"`. |

#### Response: `200 OK`
```json
{
  "audio_id": "aud_01J8XK9R2Q0000000000000001",
  "status": "completed",
  "duration_seconds": 4.25,
  "format": "wav",
  "created_at": "2026-09-27T14:32:10.123Z",
  "audio_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000001"
}
```

#### Error Responses
- `400 Bad Request`: `InvalidTextError` (empty or too long), `InvalidFormatError`, `InvalidSpeedError`.
- `401 Unauthorized`: Missing or invalid Bearer token.
- `404 Not Found`: `VoiceNotFoundError` (Voice 1 reference file missing).
- `503 Service Unavailable`: `TTSUnavailableError` (TTS backend down or crashed).

---

## 4. Audio Persistence & Replay Endpoints

### 4.1 List Audio History (Paginated)
Retrieves chronological history of generated audio files, newest first.

- **Method:** `GET`
- **Path:** `/api/v1/audio`
- **Authentication:** Optional in development / Required in production
- **Query Parameters:**
  - `page` (integer, default: `1`, min: `1`)
  - `limit` (integer, default: `20`, min: `1`, max: `100`)

#### Response: `200 OK`
```json
{
  "total": 42,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "audio_id": "aud_01J8XK9R2Q0000000000000002",
      "text": "Tell me something interesting.",
      "voice_id": "1",
      "format": "wav",
      "duration_seconds": 3.12,
      "sample_rate": 22050,
      "channels": 1,
      "created_at": "2026-09-27T14:35:00.000Z",
      "audio_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000002",
      "file_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000002/file"
    },
    {
      "audio_id": "aud_01J8XK9R2Q0000000000000001",
      "text": "Hello there! How can I help you today?",
      "voice_id": "1",
      "format": "wav",
      "duration_seconds": 2.85,
      "sample_rate": 22050,
      "channels": 1,
      "created_at": "2026-09-27T14:32:10.123Z",
      "audio_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000001",
      "file_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000001/file"
    }
  ]
}
```

---

### 4.2 Get Audio Metadata
Retrieves detailed metadata for a single generated audio item.

- **Method:** `GET`
- **Path:** `/api/v1/audio/{audio_id}`
- **Response: `200 OK`**
```json
{
  "audio_id": "aud_01J8XK9R2Q0000000000000001",
  "text": "Hello there! How can I help you today?",
  "voice_id": "1",
  "format": "wav",
  "duration_seconds": 2.85,
  "sample_rate": 22050,
  "channels": 1,
  "created_at": "2026-09-27T14:32:10.123Z",
  "file_path": "tts/output/2026/09/27/aud_01J8XK9R2Q0000000000000001.wav",
  "file_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000001/file"
}
```

#### Error Response
- `404 Not Found`: If `audio_id` does not exist in local metadata store.

---

### 4.3 Stream Audio File (Playback Replay)
Streams the physical WAV or MP3 audio file. Supports HTTP Range Requests for seekability in the frontend player.

- **Method:** `GET`
- **Path:** `/api/v1/audio/{audio_id}/file`
- **Response Headers:**
  - `Content-Type: audio/wav` (or `audio/mpeg`)
  - `Accept-Ranges: bytes`
  - `Content-Length: <filesize>`
  - `Cache-Control: public, max-age=31536000, immutable`
- **Response: `200 OK` (Full content) or `206 Partial Content` (Range request)**

---

### 4.4 Delete Audio Item
Deletes the specific audio file and its associated JSON metadata from disk.

- **Method:** `DELETE`
- **Path:** `/api/v1/audio/{audio_id}`
- **Response: `204 No Content`**
- **Error Response:**
  - `404 Not Found`: If `audio_id` does not exist.

---

## 5. Voice Management Endpoints

### 5.1 List Registered Voices
Retrieves all registered voice profiles. For V1, this targets Voice ID 1.

- **Method:** `GET`
- **Path:** `/api/v1/voices`
- **Response: `200 OK`**
```json
[
  {
    "voice_id": "1",
    "name": "Voice 1",
    "status": "ready",
    "reference_file": "reference.wav",
    "transcript": null,
    "created_at": "2026-09-27T10:00:00.000Z"
  }
]
```

---

### 5.2 Upload Voice Reference (Register Voice 1)
Uploads an audio reference sample (`.wav`) to serve as Voice ID 1's voice clone reference.

- **Method:** `POST`
- **Path:** `/api/v1/voices`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: Audio file (binary, WAV format, 16-bit or 24-bit PCM, duration 3s–30s)
  - `voice_id`: Optional string, defaults to `"1"`
  - `name`: Optional display name, defaults to `"Voice 1"`
  - `transcript`: Optional string providing the exact transcript of the reference sample

#### Response: `201 Created`
```json
{
  "voice_id": "1",
  "name": "Voice 1",
  "status": "ready",
  "reference_file": "reference.wav",
  "transcript": "Hello, this is my sample reference voice.",
  "created_at": "2026-09-27T14:40:00.000Z"
}
```

---

### 5.3 Delete Voice 1 Profile
Removes the configured Voice 1 reference audio and metadata.  
**Critical Safety Invariant:** Removing Voice 1 does **NOT** delete previously generated audio files in the audio store.

- **Method:** `DELETE`
- **Path:** `/api/v1/voices/1`
- **Response: `204 No Content`**

---

## 6. Downstream TTS Status Endpoint

### 6.1 TTS Health & Model Status
Queries the health and readiness of the internal TTS provider.

- **Method:** `GET`
- **Path:** `/api/v1/tts/status`
- **Response: `200 OK`**
```json
{
  "provider": "cosyvoice",
  "status": "ready",
  "model_loaded": true
}
```
If the model is loading or the service is down:
```json
{
  "provider": "cosyvoice",
  "status": "unavailable",
  "model_loaded": false
}
```
