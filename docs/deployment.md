# EchoMCP — Deployment & Infrastructure Guide
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Phase 0 (Architecture & Contracts)  

---

## 1. Prerequisites

- **Host Operating System:** Linux, macOS, or Windows (WSL2 recommended for Windows)
- **Docker Engine:** v24.0+
- **Docker Compose:** v2.20+
- **Hardware Requirements:**
  - **GPU Mode:** NVIDIA GPU with at least 8GB VRAM + NVIDIA Container Toolkit (`nvidia-docker2`).
  - **CPU Fallback:** Multi-core x86_64 / ARM64 CPU with at least 8GB System RAM (note: synthesis latency will be higher).
- **Cloudflare Tunnel (`cloudflared`):** Installed locally or run via container for remote Grok ingress.

---

## 2. Docker Compose Topology

The system deploys three isolated containers on the `grok-voice-network` bridge:

```
[Cloudflare Ingress]
        │
        ▼ (Port 3001)
┌──────────────────┐       ┌──────────────────┐
│   echomcp-server │ ────> │    echomcp-tts   │ (Internal Port 8080)
└──────────────────┘       └──────────────────┘
        ▲                           │
        │                           ▼
        │ (Port 3000)      [Persistent Storage Volumes]
┌──────────────────┐        ├── /app/tts/models
│ echomcp-frontend │        ├── /app/tts/voices
└──────────────────┘        └── /app/tts/output
```

### Volume Mounts
1. `tts/models` (`/app/tts/models`): Cached PyTorch weights for CosyVoice 3 model. Avoids re-downloading model checkpoints across container recreations.
2. `tts/voices` (`/app/tts/voices`): Persistent directory holding Voice ID 1 (`reference.wav` and `metadata.json`).
3. `tts/output` (`/app/tts/output`): Permanent hierarchical archive for generated `.wav` files and corresponding metadata JSON files.

---

## 3. Environment Configuration (`.env`)

A sample `.env.example` file is provided at repository root:

```ini
# Application Environment
APP_ENV=development

# MCP Server Configuration
MCP_HOST=0.0.0.0
MCP_PORT=3001

# Security Token (MUST be kept secret in production)
MCP_AUTH_TOKEN=change-me-to-a-secure-random-token

# TTS Provider Configuration
TTS_HOST=0.0.0.0
TTS_PORT=8080
TTS_BASE_URL=http://tts:8080
TTS_DEVICE=cpu # or 'cuda' for NVIDIA GPU

# Default Audio Parameters
DEFAULT_VOICE_ID=1
MAX_TEXT_LENGTH=5000
MAX_AUDIO_SECONDS=120
DEFAULT_AUDIO_FORMAT=wav
DEFAULT_SPEED=1.0

# Audio Retention Policy
AUDIO_RETENTION_ENABLED=false
AUDIO_RETENTION_DAYS=30

# Observability
LOG_LEVEL=INFO
```

---

## 4. Cloudflare Tunnel Setup

To allow Grok (running in xAI's cloud) to reach your local MCP endpoint:

### Option A: Quick Tunnel (Recommended for Development)
Run Cloudflare Quick Tunnel without an account:

```bash
cloudflared tunnel --url http://localhost:3001
```

Cloudflare will output a public HTTPS URL:
```text
https://random-word-subdomain.trycloudflare.com
```

Your Grok MCP Connector URL is then:
```text
https://random-word-subdomain.trycloudflare.com/mcp
```
*(Note: Quick Tunnel URLs rotate each time the process restarts).*

### Option B: Named Cloudflare Tunnel (Production)
For a persistent static domain (e.g., `mcp.yourdomain.com`):
```bash
cloudflared tunnel create grok-voice-bridge
cloudflared tunnel route dns grok-voice-bridge mcp.yourdomain.com
cloudflared tunnel run --url http://localhost:3001 grok-voice-bridge
```

---

## 5. CPU Fallback vs GPU Acceleration

| Feature | GPU Mode (CUDA) | CPU Fallback Mode |
| :--- | :--- | :--- |
| **Inference Latency** | 200ms – 1.2s per sentence | 3s – 8s per sentence |
| **Docker Compose Config** | Requires `deploy.resources.reservations.devices` with `capabilities: [gpu]` | Standard CPU container |
| **Environment Flag** | `TTS_DEVICE=cuda` | `TTS_DEVICE=cpu` |
| **Prerequisites** | NVIDIA Container Toolkit installed | None beyond standard Docker |
