# EchoMCP — Deployment & Infrastructure Guide
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Production-Ready Zero-Shot Voice Bridge  

---

## 1. Prerequisites & Hardware Specs

- **Host Operating System:** Linux (Ubuntu 22.04+ recommended), macOS, or Windows 10/11 (with WSL2).
- **Docker Engine:** v24.0+
- **Docker Compose:** v2.20+
- **Hardware Sizing:**
  - **GPU Mode (Recommended for Production):**
    - NVIDIA GPU with >= 8GB VRAM (e.g., RTX 3060/3070/3080/4070/4090 or datacenter T4/A10G).
    - NVIDIA Container Toolkit (`nvidia-docker2`) installed on the host.
    - Latency: ~200ms – 1.5s per sentence.
  - **CPU Mode (Fallback):**
    - Multi-core CPU (>= 4 cores) with >= 16GB System RAM (8GB absolute minimum).
    - Latency: ~3s – 8s per sentence.

---

## 2. Docker Compose Topology

The stack deploys four containerized services on the internal `grok-voice-network` bridge:

```
[Cloudflare Ingress (echomcp-tunnel)]
        │
        ▼ (Port 3001)
┌──────────────────┐       ┌──────────────────┐
│   echomcp-server │ ────> │    echomcp-tts   │ (Internal Port 8080)
└──────────────────┘       └──────────────────┘
        ▲                           │
        │                           ▼
        │ (Port 3000)      [Persistent Storage Volumes]
┌──────────────────┐        ├── /app/models   (CosyVoice-300M-Instruct weights)
│ echomcp-frontend │        ├── /app/voices   (Voice ID 1 reference audio)
└──────────────────┘        └── /app/output   (Permanent audio archive)
```

### Volume Mounts
1. `tts/models` (`/app/models`): Cached PyTorch weights for CosyVoice-300M-Instruct. Auto-downloaded from ModelScope/HuggingFace on first start and cached persistently.
2. `tts/voices` (`/app/voices`): Persistent voice profile storage. Voice ID 1 (`tts/voices/1/reference.wav`) is pre-packaged and ready to clone.
3. `tts/output` (`/app/output`): Permanent hierarchical archive for generated `.wav` files and corresponding metadata JSON files.

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
TTS_DEVICE=cpu # Set to 'cuda' for NVIDIA GPU acceleration

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

## 4. Deploying on a High-Spec GPU PC

To run with full NVIDIA CUDA acceleration:

1. In `.env`, set:
   ```ini
   TTS_DEVICE=cuda
   ```
2. In `docker-compose.yml`, uncomment the GPU reservation block under the `tts` service:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```
3. Build and launch:
   ```bash
   docker compose up -d --build
   ```

---

## 5. Cloudflare Tunnel Ingress

To allow Grok (running in xAI's cloud) to reach your local MCP endpoint:

### Option A: Integrated Quick Tunnel (Default in Docker Compose)
The `echomcp-tunnel` service automatically provisions a Cloudflare Quick Tunnel on container startup:
```bash
docker compose logs tunnel
```
Look for the output:
```text
https://<random-subdomain>.trycloudflare.com
```
Your Grok MCP Connector URL is:
```text
https://<random-subdomain>.trycloudflare.com/mcp
```

### Option B: Named Cloudflare Tunnel (Dedicated Domain)
For a persistent static domain (e.g., `mcp.yourdomain.com`):
```bash
cloudflared tunnel create grok-voice-bridge
cloudflared tunnel route dns grok-voice-bridge mcp.yourdomain.com
cloudflared tunnel run --url http://localhost:3001 grok-voice-bridge
```

---

## 6. CPU Fallback vs GPU Acceleration Comparison

| Feature | GPU Mode (CUDA) | CPU Fallback Mode |
| :--- | :--- | :--- |
| **Inference Latency** | ~200ms – 1.5s per sentence | ~3s – 8s per sentence |
| **Docker Compose Config** | Requires `deploy.resources.reservations.devices` with `capabilities: [gpu]` | Standard CPU container (default) |
| **Environment Flag** | `TTS_DEVICE=cuda` | `TTS_DEVICE=cpu` |
| **Prerequisites** | NVIDIA Container Toolkit installed | Standard Docker only |

