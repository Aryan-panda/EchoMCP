from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from app.dependencies import get_audio_service
from app.services.audio_service import AudioService
from app.models.audio import PaginatedAudioResponse, AudioMetadata
from app.utils.ids import is_valid_audio_id

router = APIRouter(prefix="/api/v1/audio", tags=["Audio"])

@router.get("", response_model=PaginatedAudioResponse)
def list_audio(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    audio_svc: AudioService = Depends(get_audio_service),
):
    return audio_svc.list_audio(page=page, limit=limit)

@router.get("/{audio_id}", response_model=AudioMetadata)
def get_audio_metadata(
    audio_id: str,
    audio_svc: AudioService = Depends(get_audio_service),
):
    if not is_valid_audio_id(audio_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio ID format")

    meta = audio_svc.get_audio_metadata(audio_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio record not found")
    return meta

@router.get("/{audio_id}/file")
def get_audio_file(
    audio_id: str,
    audio_svc: AudioService = Depends(get_audio_service),
):
    if not is_valid_audio_id(audio_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio ID format")

    file_path = audio_svc.get_audio_file_path(audio_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk")

    media_type = "audio/wav" if file_path.suffix.lower() == ".wav" else "audio/mpeg"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
        headers={"Accept-Ranges": "bytes"}
    )

@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audio(
    audio_id: str,
    audio_svc: AudioService = Depends(get_audio_service),
):
    if not is_valid_audio_id(audio_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio ID format")

    deleted = audio_svc.delete_audio(audio_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio record not found")
    return None
