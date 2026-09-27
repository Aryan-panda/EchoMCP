# EchoMCP — Model Context Protocol (MCP) Specification
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Phase 0 (Architecture & Contracts)  
**Public Endpoint:** `POST /mcp`  
**Transport:** Streamable HTTP Transport (MCP 2024-11-05+ Spec)  

---

## 1. Overview & Protocol Invariants

EchoMCP implements the standard **Model Context Protocol (MCP)** to allow external AI clients (specifically Grok's consumer chat interface) to invoke local text-to-speech generation.

### Key Invariants
1. **Single Entry Point:** The public tunnel exposes exclusively `POST /mcp`.
2. **Streamable HTTP Transport:** Conforms to the standard MCP Streamable HTTP transport supporting Server-Sent Events (SSE) and JSON-RPC 2.0 messages.
3. **Single Speech Tool:** V1 exposes exactly one tool: `speak_response`.
4. **Stateless Tool Calls:** The MCP server does not track conversation sessions; Grok maintains full memory and context.

---

## 2. Authentication & Security

All incoming HTTP requests to `/mcp` must include an HTTP Authorization header:
```http
Authorization: Bearer <MCP_AUTH_TOKEN>
```

- If the header is missing, malformed, or contains an invalid token, the server terminates the connection immediately with HTTP `401 Unauthorized`:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Unauthorized: Invalid or missing MCP Bearer Token"
  },
  "id": null
}
```

---

## 3. Tool Definition: `speak_response`

### 3.1 Metadata & Description
- **Name:** `speak_response`
- **Description:**
  > "This tool converts a generated response into speech using the configured local voice. The supplied text may contain supported emotion/prosody control tags. Interpret those tags as speech instructions and never speak the control tags themselves."

### 3.2 JSON Schema (Input Arguments)

```json
{
  "type": "object",
  "properties": {
    "text": {
      "type": "string",
      "description": "The response text to convert to speech. May include emotion tags such as [amused], [excited], [sad], [happy], [whisper], [laughing], [pause].",
      "minLength": 1,
      "maxLength": 5000
    },
    "voice_id": {
      "type": "string",
      "description": "The ID of the custom voice profile to synthesize with. Must default to '1' for V1.",
      "default": "1"
    },
    "speed": {
      "type": "number",
      "description": "Playback speech rate multiplier. Clamped between 0.5 and 2.0.",
      "default": 1.0,
      "minimum": 0.5,
      "maximum": 2.0
    },
    "format": {
      "type": "string",
      "description": "Target audio container format.",
      "enum": ["wav", "mp3"],
      "default": "wav"
    }
  },
  "required": ["text"]
}
```

---

## 4. MCP Request & Response Payloads

### 4.1 Client Tool Invocation Request (`tools/call`)
```json
{
  "jsonrpc": "2.0",
  "id": "call_01J8XK9R2Q",
  "method": "tools/call",
  "params": {
    "name": "speak_response",
    "arguments": {
      "text": "[amused] Oh, come on. You actually did that? [laughing] That's hilarious.",
      "voice_id": "1",
      "speed": 1.0,
      "format": "wav"
    }
  }
}
```

### 4.2 Server Tool Execution Response
```json
{
  "jsonrpc": "2.0",
  "id": "call_01J8XK9R2Q",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Audio generated successfully (duration: 4.83s, id: aud_01J8XK9R2Q0000000000000001)."
      }
    ],
    "structured_data": {
      "audio_id": "aud_01J8XK9R2Q0000000000000001",
      "status": "completed",
      "format": "wav",
      "duration_seconds": 4.83,
      "audio_url": "/api/v1/audio/aud_01J8XK9R2Q0000000000000001"
    },
    "isError": false
  }
}
```

---

## 5. Emotion / Prosody Vocabulary & Rules

The MCP server parses and intercepts the following controlled tags:

| Tag | Intended Prosody / Emotion Effect | Action on Tag Text |
| :--- | :--- | :--- |
| `[happy]` | Upbeat pitch contour, elevated energy | Stripped from spoken text |
| `[amused]` | Light chuckle undertone, smiling vocal tract | Stripped from spoken text |
| `[excited]` | Rapid tempo, elevated pitch variance | Stripped from spoken text |
| `[sad]` | Slower rate, falling inflection, lower resonance | Stripped from spoken text |
| `[angry]` | Harsh vocal onset, compressed dynamics | Stripped from spoken text |
| `[whisper]` | Low turbulence, breathy phonation | Stripped from spoken text |
| `[laughing]` | Brief vocalized laughter burst | Stripped from spoken text |
| `[pause]` | Inserts 450ms–700ms acoustic silence | Stripped from spoken text |

### Tag Handling Invariants
1. **Never Spoken:** Control tags are never sent to the acoustic phonemizer as plain text words.
2. **Robustness:** Unknown tags (e.g. `[curious]`) are safely filtered out, preserving all surrounding words without crashing.
3. **Punctuation Preservation:** Commas, question marks, exclamation points, and ellipses are strictly preserved.

---

## 6. Grok Consumer Integration Setup

### 6.1 Custom MCP Connector Configuration
In the Grok consumer interface:
1. Navigate to **Settings** → **Connectors** (or **MCP Integrations**).
2. Choose **Add Custom MCP Server**.
3. **Server URL:** `https://<your-subdomain>.trycloudflare.com/mcp`
4. **Transport:** HTTP / Streamable HTTP.
5. **Authorization Header:**
   ```
   Authorization: Bearer <your-configured-MCP_AUTH_TOKEN>
   ```

### 6.2 System Prompt / Conversation Instructions
Provide the following instruction to Grok at the beginning of the conversation:

```markdown
For this conversation, when generating responses for spoken output, use supported emotion/prosody tags where appropriate and invoke the connected speech tool after generating the response.

The speech tool interprets these tags and does not speak the tags themselves.

Use Voice ID 1.
```

---

## 7. Audio Playback Capability Requirement

There are two distinct client integration paths:

1. **Path A (Grok Native Audio Playback):**
   - If Grok's consumer chat interface supports rendering inline HTML5 audio controls from MCP tool return payloads, the audio is playable directly within the chat transcript.
2. **Path B (Local Web Dashboard Fallback & Permanent Audio Archive):**
   - If Grok does not natively play custom MCP audio, the user relies on the local **EchoMCP Web Dashboard** (`http://localhost:3000`), which automatically detects new audio entries and provides full scrub/play/pause/download capabilities.
   - **Crucial Rule:** The underlying `Grok -> MCP -> TTS -> Audio Store` pipeline remains identical in both cases.
