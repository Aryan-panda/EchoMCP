import io
import math
import struct
import wave
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("tts-service")

app = FastAPI(title="EchoMCP TTS Engine", version="1.0.0")

class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice_id: str = Field(default="1")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    format: str = Field(default="wav")
    emotion: Optional[str] = None

def generate_mock_wav(duration_seconds: float = 2.0, sample_rate: int = 22050, freq: float = 440.0) -> bytes:
    """Generate a valid, non-empty PCM 16-bit Mono WAV file in memory."""
    num_samples = int(duration_seconds * sample_rate)
    buffer = io.BytesIO()
    
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)      # Mono
        wav_file.setsampwidth(2)      # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            # Generate a soft decayed tone
            envelope = math.exp(-3.0 * (i / num_samples))
            val = int(envelope * 8000.0 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            frames.extend(struct.pack("<h", max(-32768, min(32767, val))))
            
        wav_file.writeframes(frames)
        
    return buffer.getvalue()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status():
    return {
        "provider": "mock",
        "status": "ready",
        "model_loaded": True
    }

@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    logger.info(f"Synthesizing text: '{req.text[:40]}...' for voice: {req.voice_id} (speed: {req.speed})")
    
    # Calculate approximate duration based on word count: ~3 words per second / speed
    words = len(req.text.split())
    duration = max(1.0, min(30.0, (words / 3.0) / req.speed))
    
    # Generate valid WAV audio
    wav_bytes = generate_mock_wav(duration_seconds=duration, sample_rate=22050)
    
    headers = {
        "X-Audio-Duration": str(round(duration, 2)),
        "X-Sample-Rate": "22050",
        "X-Channels": "1"
    }
    return Response(content=wav_bytes, media_type="audio/wav", headers=headers)

@app.post("/voices/register")
def register_voice(voice_id: str = "1", name: str = "Voice 1"):
    logger.info(f"Registered voice profile {voice_id} ({name})")
    return {"voice_id": voice_id, "name": name, "status": "ready"}

@app.get("/voices")
def list_voices():
    return [{"voice_id": "1", "name": "Voice 1", "status": "ready"}]

@app.delete("/voices/{voice_id}")
def delete_voice(voice_id: str):
    logger.info(f"Deleted voice profile {voice_id}")
    return {"voice_id": voice_id, "status": "deleted"}

