# EchoMCP — Grok MCP Bridge for Custom Voice

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/phase-Phase%200%20Passed-brightgreen.svg)](#development-phases)
[![Architecture](https://img.shields.io/badge/architecture-Clean%20%26%20Decoupled-orange.svg)](docs/architecture.md)

EchoMCP (Grok Voice Bridge) adds an expressive, local custom-voice speech synthesis layer to normal Grok consumer chat via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).

---

## 🎯 System Objective

**Grok remains the brain. EchoMCP provides the voice.**

- **Grok owns:** Conversation history, context, reasoning, personality, world knowledge, and response generation.
- **EchoMCP owns:** Speech synthesis, emotion and prosody interpretation, custom voice cloning profiles, filesystem-backed audio persistence, audio replay, and local administration.

EchoMCP does **not** duplicate Grok's memory, inject another LLM, perform RAG, run vector databases, or replace Grok's chat UI.

```
User
  ↓
Normal Grok consumer chat
  ↓
Grok generates response
  ↓
Grok invokes custom MCP speech tool (speak_response)
  ↓
Cloudflare Tunnel (Public HTTPS Ingress)
  ↓
Local MCP Server (:3001)
  ↓
Emotion/Prosody Parser
  ↓
TTS Provider (CosyVoice 3 / Swappable)
  ↓
Voice ID 1
  ↓
Generated Audio (WAV/MP3)
  ↓
Persistent Local Audio Store
  ↓
Audio Playback / Replay (Local Web Dashboard :3000)
```

---

## 📑 Documentation Index

- [Architecture & Sequence Diagrams](docs/architecture.md)
- [REST API Specification](docs/api.md)
- [Model Context Protocol (MCP) Contract](docs/mcp.md)
- [Domain Data Models & Schemas](docs/data_models.md)
- [Deployment & Infrastructure Guide](docs/deployment.md)
- [Testing Strategy & Phase Gates](docs/testing.md)
- [Troubleshooting & Diagnostics](docs/troubleshooting.md)

---

## 🛠️ Technology Stack

- **Backend:** Python 3.12+, FastAPI, MCP Python SDK, Streamable HTTP Transport, Pydantic v2, `httpx`, `asyncio`, `pytest`.
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS.
- **TTS Layer:** Swappable `TTSProvider` abstraction (default: CosyVoice 3).
- **Infrastructure:** Docker, Docker Compose, Cloudflare Tunnel.

---

## 🔒 Security Posture

- **Bearer Authentication:** Public MCP endpoint strictly enforces `Authorization: Bearer <MCP_AUTH_TOKEN>`.
- **Network Isolation:** Downstream TTS service (port 8080) is on an internal Docker bridge network and is **never** exposed to the host or internet.
- **Input Clamping:** Text length constrained to 5,000 characters; speed clamped to `[0.5, 2.0]`.
- **Sandboxed Storage:** Strict path traversal prevention on audio and voice asset storage.
