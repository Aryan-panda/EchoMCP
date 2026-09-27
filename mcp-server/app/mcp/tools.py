from app.models.speech import MCPSpeakToolInput, MCPSpeakToolOutput, SpeechRequest, AudioFormat
from app.services.speech_service import SpeechService

SPEAK_RESPONSE_TOOL_DEF = {
    "name": "speak_response",
    "description": (
        "This tool converts a generated response into speech using the configured local voice. "
        "The supplied text may contain supported emotion/prosody control tags. "
        "Interpret those tags as speech instructions and never speak the control tags themselves."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The response text to convert to speech. May include emotion tags such as [amused], [excited], [sad], [happy], [whisper], [laughing], [pause].",
                "minLength": 1,
                "maxLength": 5000
            },
            "voice_id": {
                "type": "string",
                "description": "The ID of the custom voice profile to synthesize with. Must default to '1' for V1.",
                "default": "1"
            },
            "speed": {
                "type": "number",
                "description": "Playback speech rate multiplier. Clamped between 0.5 and 2.0.",
                "default": 1.0,
                "minimum": 0.5,
                "maximum": 2.0
            },
            "format": {
                "type": "string",
                "description": "Target audio container format.",
                "enum": ["wav", "mp3"],
                "default": "wav"
            }
        },
        "required": ["text"]
    }
}

async def execute_speak_response(
    arguments: dict,
    speech_service: SpeechService,
    request_id: str
) -> dict:
    """Execute the speak_response tool call."""
    validated = MCPSpeakToolInput(**arguments)
    speech_req = SpeechRequest(
        text=validated.text,
        voice_id=validated.voice_id,
        speed=validated.speed,
        format=validated.format,
    )
    res, metrics = await speech_service.speak(speech_req, request_id=request_id)
    return {
        "content": [
            {
                "type": "text",
                "text": f"Audio generated successfully (duration: {res.duration_seconds}s, id: {res.audio_id})."
            }
        ],
        "structured_data": {
            "audio_id": res.audio_id,
            "status": res.status.value,
            "format": res.format.value,
            "duration_seconds": res.duration_seconds,
            "audio_url": res.audio_url
        },
        "isError": False
    }
