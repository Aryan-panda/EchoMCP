from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from app.dependencies import get_voice_service, get_tts_provider
from app.services.voice_service import VoiceService
from app.services.providers.base import TTSProvider
from app.models.voice import VoiceMetadata, TTSStatusResponse

router = APIRouter(prefix="/api/v1", tags=["Voices"])

@router.get("/voices", response_model=list[VoiceMetadata])
def list_voices(voice_svc: VoiceService = Depends(get_voice_service)):
    return voice_svc.list_voices()

@router.post("/voices", response_model=VoiceMetadata, status_code=status.HTTP_201_CREATED)
async def upload_voice_reference(
    file: UploadFile = File(...),
    voice_id: str = Form(default="1"),
    name: str = Form(default="Voice 1"),
    transcript: Optional[str] = Form(default=None),
    voice_svc: VoiceService = Depends(get_voice_service),
    tts: TTSProvider = Depends(get_tts_provider),
):
    if voice_id != "1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="V1 only supports registration for Voice ID '1'."
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    try:
        meta = voice_svc.register_voice_reference(
            voice_id=voice_id,
            name=name,
            audio_bytes=content,
            transcript=transcript,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Notify downstream TTS if applicable
    try:
        await tts.register_voice(voice_id=voice_id, name=name, file_path="reference.wav")
    except Exception:
        pass

    return meta

@router.delete("/voices/1", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_1(
    voice_svc: VoiceService = Depends(get_voice_service),
    tts: TTSProvider = Depends(get_tts_provider),
):
    deleted = voice_svc.delete_voice("1")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice 1 not found")

    try:
        await tts.delete_voice("1")
    except Exception:
        pass

    return None

@router.get("/tts/status", response_model=TTSStatusResponse)
async def get_tts_status(tts: TTSProvider = Depends(get_tts_provider)):
    try:
        stat = await tts.status()
        return TTSStatusResponse(
            provider=stat.get("provider", "cosyvoice"),
            status=stat.get("status", "ready"),
            model_loaded=stat.get("model_loaded", True)
        )
    except Exception as e:
        return TTSStatusResponse(
            provider="cosyvoice",
            status="unavailable",
            model_loaded=False
        )
