import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from engine import CosyVoiceEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("echomcp-tts")

app = FastAPI(title="EchoMCP CosyVoice Engine", version="1.0.0")

# Initialize synthesizer engine
device = os.getenv("TTS_DEVICE", "cpu")
models_dir = Path(os.getenv("MODELS_DIR", "models" if Path("models").exists() else "tts/models"))
voices_dir = Path(os.getenv("VOICES_DIR", "voices" if Path("voices").exists() else "tts/voices"))

engine = CosyVoiceEngine(models_dir=models_dir, device=device)

class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(default="1")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    format: str = Field(default="wav")
    emotion: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status_endpoint():
    return {
        "provider": "cosyvoice",
        "status": "ready" if engine.model_loaded else "loading",
        "model_loaded": engine.model_loaded,
        "device": engine.device
    }

@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Synthesize text cannot be empty or whitespace"
        )

    # Locate reference voice for Voice ID conditioning
    ref_path = voices_dir / req.voice_id / "reference.wav"

    try:
        audio_bytes, duration = engine.synthesize_speech(
            text=clean_text,
            reference_wav_path=ref_path if ref_path.exists() else None,
            speed=req.speed,
            emotion=req.emotion
        )
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis engine failure: {str(e)}"
        )

    headers = {
        "Content-Type": "audio/wav",
        "X-Audio-Duration": str(duration),
        "X-Sample-Rate": str(engine.sample_rate),
        "X-Channels": "1"
    }

    logger.info(f"Synthesized {duration}s audio for voice '{req.voice_id}' (text: '{clean_text[:30]}...')")
    return Response(content=audio_bytes, media_type="audio/wav", headers=headers)

@app.get("/voices")
def list_voices():
    voices = []
    if voices_dir.exists():
        for d in voices_dir.iterdir():
            if d.is_dir() and (d / "reference.wav").exists():
                voices.append({"voice_id": d.name, "name": f"Voice {d.name}", "status": "ready"})
    if not voices:
        voices = [{"voice_id": "1", "name": "Voice 1", "status": "ready"}]
    return voices

@app.post("/voices/register")
def register_voice(voice_id: str = "1", name: str = "Voice 1"):
    target = voices_dir / voice_id
    target.mkdir(parents=True, exist_ok=True)
    return {"voice_id": voice_id, "name": name, "status": "ready"}

@app.delete("/voices/{voice_id}")
def delete_voice(voice_id: str):
    target = voices_dir / voice_id
    if target.exists():
        ref = target / "reference.wav"
        if ref.exists():
            ref.unlink()
        return {"voice_id": voice_id, "status": "deleted"}
    return {"voice_id": voice_id, "status": "not_found"}
