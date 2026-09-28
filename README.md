# EchoMCP — Grok MCP Bridge for Custom Voice

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-97%20passed-brightgreen.svg)](docs/testing.md)
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
TTS Provider (CosyVoice-300M-Instruct Zero-Shot Engine)
  ↓
Voice ID 1 (tts/voices/1/reference.wav)
  ↓
Generated Audio (WAV/MP3)
  ↓
Persistent Local Audio Store
  ↓
Audio Playback / Replay (Local Web Dashboard :3000)
```

---

## 🚀 Quick Start (Setup Guide)

Follow these steps to deploy EchoMCP on your machine. For human-like, near-zero latency voice cloning and real-time emotion execution, an NVIDIA GPU (RTX 3060/3070/3080/4070/4090 or datacenter GPU) is recommended.

### 1. Prerequisites
- [Docker Engine](https://docs.docker.com/engine/install/) (v24+) & Docker Compose (v2.20+)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) (for GPU acceleration)
- Git

### 2. Configure Environment
Clone the repository and copy the environment template:
```bash
git clone https://github.com/Aryan-panda/EchoMCP.git
cd EchoMCP
cp .env.example .env
```
Open `.env` and verify your settings:
```ini
MCP_AUTH_TOKEN=your-secure-random-token-here
TTS_DEVICE=cuda   # Set to 'cuda' for NVIDIA GPU
COSYVOICE_MODEL=CosyVoice-300M-Instruct
```

> **Pre-configured Voice ID 1:** Your reference voice audio is already pre-configured and tracked at `tts/voices/1/reference.wav`. You do not need to record or upload anything before your first run!

### 3. Enable GPU Acceleration & Launch
In `docker-compose.yml`, ensure the GPU block under `tts` is active:
```yaml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Launch all services:
```bash
docker compose up -d --build
```
*On first startup, the TTS container will download the official CosyVoice-300M-Instruct neural weights to `./tts/models` and cache them for instant subsequent restarts.*

### 4. Connect Grok to EchoMCP
1. Inspect the Cloudflare Tunnel logs to obtain your public HTTPS URL:
   ```bash
   docker compose logs tunnel
   ```
   Look for the line: `https://<random-subdomain>.trycloudflare.com`
2. Open **Grok** → **Settings** → **Connectors / MCP**.
3. Click **Add Custom MCP Server**:
   - **URL:** `https://<random-subdomain>.trycloudflare.com/mcp`
   - **Auth Header:** `Authorization: Bearer <your-configured-MCP_AUTH_TOKEN>`
4. Direct Grok with the following system instruction:
   > *"When responding to speech prompts, use emotion tags like [amused], [whisper], [happy], or [excited] and invoke the connected speech tool (speak_response) to speak with Voice ID 1."*

### 5. Access the Web Dashboard
Open [http://localhost:3000](http://localhost:3000) in your browser:
- Monitor live system health (MCP Server, CosyVoice Engine, Voice ID 1).
- Listen to real-time audio generations and replay historical speech outputs.
- Test synthesis directly with custom emotion tags (`[happy]`, `[whisper]`, `[amused]`, `[excited]`).

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
- **TTS Layer:** Alibaba FunAudioLLM CosyVoice-300M-Instruct zero-shot voice cloning engine with neural emotion/prosody instruction-following via swappable `TTSProvider` abstraction.
- **Infrastructure:** Docker, Docker Compose, Cloudflare Tunnel (`cloudflared`).

---

## 🔒 Security Posture

- **Bearer Authentication:** Public MCP endpoint strictly enforces `Authorization: Bearer <MCP_AUTH_TOKEN>`.
- **Network Isolation:** Downstream TTS service (port 8080) is on an internal Docker bridge network and is **never** exposed to the host or internet.
- **Input Clamping:** Text length constrained to 5,000 characters; speed clamped to `[0.5, 2.0]`.
- **Sandboxed Storage:** Strict path traversal prevention on audio and voice asset storage.
