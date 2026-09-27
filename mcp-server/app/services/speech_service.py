import time
import asyncio
import logging
from typing import Optional
from app.config import settings
from app.models.speech import (
    SpeechRequest,
    SpeechResponse,
    AudioFormat,
    SynthesisStatus,
    LatencyMetrics,
)
from app.services.emotion_parser import parse_emotion_text
from app.services.providers.base import TTSProvider
from app.services.audio_service import AudioService
from app.services.voice_service import VoiceService
from app.utils.ids import generate_request_id, generate_audio_id
from app.utils.logging import JSONFormatter

logger = logging.getLogger("echomcp.speech_service")

class SpeechService:
    def __init__(
        self,
        tts_provider: TTSProvider,
        audio_service: AudioService,
        voice_service: VoiceService,
    ):
        self.tts = tts_provider
        self.audio = audio_service
        self.voices = voice_service
        self._semaphore = asyncio.Semaphore(1)

    async def speak(self, req: SpeechRequest, request_id: Optional[str] = None) -> tuple[SpeechResponse, LatencyMetrics]:
        req_id = request_id or generate_request_id()
        t_received = time.perf_counter()

        # Step 1: Parse emotions & clean text
        t_mcp_start = time.perf_counter()
        parsed = parse_emotion_text(req.text)
        if not parsed.clean_text:
            raise ValueError("Input text contains no pronounceable content after removing emotion tags.")

        mcp_overhead_ms = (t_mcp_start - t_received) * 1000.0

        # Step 2: Validate target voice
        voice_id = req.voice_id or settings.DEFAULT_VOICE_ID
        if not self.voices.is_voice_ready(voice_id):
            logger.warning(f"Voice reference for {voice_id} missing; synthesis proceeding with default parameters.")

        # Step 3: Invoke TTS synthesis protected by concurrency semaphore
        t_tts_start = time.perf_counter()
        primary_emotion = parsed.segments[0].emotion.value if parsed.segments else None
        
        async with self._semaphore:
            audio_bytes, meta = await self.tts.synthesize(
                text=parsed.clean_text,
                voice_id=voice_id,
                speed=req.speed,
                format=req.format.value,
                emotion=primary_emotion,
            )
        t_tts_end = time.perf_counter()
        tts_latency_ms = (t_tts_end - t_tts_start) * 1000.0

        # Step 4: Persist audio record
        t_storage_start = time.perf_counter()
        audio_id = generate_audio_id()
        saved_record = self.audio.save_audio(
            audio_id=audio_id,
            text=parsed.clean_text,
            audio_bytes=audio_bytes,
            voice_id=voice_id,
            audio_format=req.format,
            duration_seconds=meta.get("duration_seconds", 2.0),
            sample_rate=meta.get("sample_rate", 22050),
            channels=meta.get("channels", 1),
        )
        t_storage_end = time.perf_counter()
        storage_latency_ms = (t_storage_end - t_storage_start) * 1000.0

        total_latency_ms = (time.perf_counter() - t_received) * 1000.0

        metrics = LatencyMetrics(
            mcp_overhead_ms=round(mcp_overhead_ms, 2),
            tts_latency_ms=round(tts_latency_ms, 2),
            storage_latency_ms=round(storage_latency_ms, 2),
            total_latency_ms=round(total_latency_ms, 2),
        )

        logger.info(
            f"Speech generated: {audio_id} in {metrics.total_latency_ms}ms "
            f"(MCP: {metrics.mcp_overhead_ms}ms, TTS: {metrics.tts_latency_ms}ms, Store: {metrics.storage_latency_ms}ms)",
            extra={
                "request_id": req_id,
                "metrics": metrics.model_dump(),
                "extra_data": {
                    "audio_id": audio_id,
                    "voice_id": voice_id,
                    "text_len": len(parsed.clean_text),
                }
            }
        )

        response = SpeechResponse(
            audio_id=saved_record.audio_id,
            status=SynthesisStatus.COMPLETED,
            duration_seconds=saved_record.duration_seconds,
            format=saved_record.format,
            created_at=saved_record.created_at,
            audio_url=f"/api/v1/audio/{saved_record.audio_id}",
        )

        return response, metrics
