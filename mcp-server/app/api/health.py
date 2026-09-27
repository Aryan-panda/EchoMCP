from fastapi import APIRouter, Depends, Response, status
from app.dependencies import get_tts_provider, get_voice_service, get_audio_service
from app.services.providers.base import TTSProvider
from app.services.voice_service import VoiceService
from app.services.audio_service import AudioService

router = APIRouter(tags=["System"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/ready")
async def ready(
    response: Response,
    tts: TTSProvider = Depends(get_tts_provider),
    voice_svc: VoiceService = Depends(get_voice_service),
    audio_svc: AudioService = Depends(get_audio_service),
):
    # Check 1: MCP Server is alive (self)
    mcp_ready = True

    # Check 2: Downstream TTS connectivity
    tts_ready = False
    try:
        health_resp = await tts.health()
        tts_ready = health_resp.get("status") == "ok"
    except Exception:
        tts_ready = False

    # Check 3: Voice ID 1 reference audio
    voice_1_ready = voice_svc.is_voice_ready("1")

    # Check 4: Audio storage writeability
    audio_store_ready = False
    try:
        test_file = audio_svc.output_dir / ".write_probe"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        audio_store_ready = True
    except Exception:
        audio_store_ready = False

    all_ready = mcp_ready and tts_ready and voice_1_ready and audio_store_ready

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "mcp": mcp_ready,
        "tts": tts_ready,
        "voice_1": voice_1_ready,
        "audio_store": audio_store_ready,
        "ready": all_ready
    }

@router.get("/version")
def version():
    return {
        "name": "grok-voice-bridge",
        "version": "1.0.0"
    }
