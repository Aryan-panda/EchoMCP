from functools import lru_cache
from fastapi import Depends
from app.config import settings
from app.services.providers.cosyvoice import CosyVoiceProvider
from app.services.providers.base import TTSProvider
from app.services.audio_service import AudioService
from app.services.voice_service import VoiceService
from app.services.speech_service import SpeechService

@lru_cache()
def get_tts_provider() -> TTSProvider:
    return CosyVoiceProvider(base_url=settings.TTS_BASE_URL)

@lru_cache()
def get_audio_service() -> AudioService:
    return AudioService(output_dir=settings.output_path)

@lru_cache()
def get_voice_service() -> VoiceService:
    return VoiceService(voices_dir=settings.voices_path)

def get_speech_service(
    tts_provider: TTSProvider = Depends(get_tts_provider),
    audio_service: AudioService = Depends(get_audio_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> SpeechService:
    return SpeechService(
        tts_provider=tts_provider,
        audio_service=audio_service,
        voice_service=voice_service,
    )
