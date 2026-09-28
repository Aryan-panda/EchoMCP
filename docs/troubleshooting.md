# EchoMCP — Troubleshooting & Diagnostic Guide
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Phase 0 (Architecture & Contracts)  

---

## 1. Diagnostic Decision Tree

```
Issue Detected
  ├── Grok returns "Tool invocation failed"
  │     ├── Check Cloudflare Tunnel (`cloudflared` logs)
  │     ├── Verify Bearer Token in Grok connector matches MCP_AUTH_TOKEN
  │     └── Verify MCP server is listening on port 3001
  │
  ├── Audio synthesis returns HTTP 503 / TTSUnavailableError
  │     ├── Check TTS container status: `docker compose ps`
  │     ├── Verify CosyVoice-300M-Instruct weights downloaded to `tts/models`
  │     └── Check GPU memory (OOM) or CPU starvation in TTS container logs
  │
  ├── Voice ID 1 returns 404 / VoiceNotFoundError
  │     ├── Check existence of `tts/voices/1/reference.wav`
  │     └── Upload reference audio via Web Dashboard or POST /api/v1/voices
  │
  └── Audio generated but cannot be replayed
        ├── Check write permissions in `tts/output/`
        └── Verify JSON metadata in `tts/output/metadata/`
```

---

## 2. Common Issues & Solutions

### 2.1 Issue: Grok Fails to Connect to MCP Server
- **Symptoms:** Grok consumer UI reports `Connector unreachable` or `HTTP 401 Unauthorized`.
- **Root Causes:**
  1. Quick Tunnel URL was regenerated after restarting `cloudflared`.
  2. Missing or incorrect `Authorization: Bearer <token>` in Grok connector settings.
  3. Cloudflare tunnel routed to port 3000 (frontend) instead of port 3001 (MCP server).
- **Remediation:**
  1. Confirm the public tunnel endpoint by checking terminal logs where `cloudflared` is running.
  2. Test manually using curl:
     ```bash
     curl -X POST https://<subdomain>.trycloudflare.com/mcp \
       -H "Authorization: Bearer $MCP_AUTH_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"jsonrpc": "2.0", "id": "1", "method": "tools/list"}'
     ```

---

### 2.2 Issue: TTS Container Crashes or Out-of-Memory (OOM)
- **Symptoms:** Container `echomcp-tts` exits with code 137 or logs show `CUDA out of memory`.
- **Root Causes:**
  1. Large batch or prompt text exceeded GPU VRAM capacity.
  2. Concurrent synthesis requests collided on a single GPU stream.
- **Remediation:**
  1. Switch to CPU fallback mode by setting `TTS_DEVICE=cpu` in `.env`.
  2. Enforce concurrency limiting via `MAX_CONCURRENT_SYNTHESIS=1` in `app/config.py`.

---

### 2.3 Issue: Control Tags Being Spoken Aloud
- **Symptoms:** Generated audio literally speaks the words *"bracket amused bracket"*.
- **Root Causes:**
  1. Emotion parser was bypassed or input text was passed directly to the TTS backend without segmentation.
- **Remediation:**
  1. Verify emotion regex strips all brackets and tags in `mcp-server/app/services/emotion_parser.py`.
  2. Run `pytest mcp-server/tests/unit/test_emotion_parser.py`.

---

### 2.4 Issue: Older Audio Disappears from History
- **Symptoms:** Replay fails on previous conversation turns.
- **Root Causes:**
  1. `AUDIO_RETENTION_ENABLED` was set to `true` with an aggressive threshold during development.
- **Remediation:**
  1. Ensure `AUDIO_RETENTION_ENABLED=false` in `.env` for development.
  2. Verify directory persistence mounts in `docker-compose.yml`.
