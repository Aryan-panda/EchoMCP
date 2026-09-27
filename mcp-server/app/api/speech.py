from fastapi import APIRouter, Depends, HTTPException, status
from app.models.speech import SpeechRequest, SpeechResponse
from app.dependencies import get_speech_service
from app.services.speech_service import SpeechService
from app.utils.ids import generate_request_id

router = APIRouter(prefix="/api/v1", tags=["Speech"])

@router.post("/speak", response_model=SpeechResponse)
async def speak(
    req: SpeechRequest,
    svc: SpeechService = Depends(get_speech_service)
):
    request_id = generate_request_id()
    try:
        response, metrics = await svc.speak(req, request_id=request_id)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Speech synthesis error: {str(e)}"
        )
