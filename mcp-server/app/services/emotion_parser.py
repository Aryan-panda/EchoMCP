import re
from typing import Optional
from app.models.speech import SupportedEmotion, EmotionSegment, ParsedSpeech

# Regex for tags like [happy], [whisper], [pause], [pause:800], [laughter]
TAG_PATTERN = re.compile(r"\[([a-zA-Z_]+)(?::(\d+))?\]", re.IGNORECASE)

# Mapping of accepted tag strings (case-insensitive) to SupportedEmotion
VALID_EMOTIONS: dict[str, SupportedEmotion] = {
    "happy": SupportedEmotion.HAPPY,
    "amused": SupportedEmotion.AMUSED,
    "excited": SupportedEmotion.EXCITED,
    "sad": SupportedEmotion.SAD,
    "angry": SupportedEmotion.ANGRY,
    "whisper": SupportedEmotion.WHISPER,
    "laughing": SupportedEmotion.LAUGHING,
    "laughter": SupportedEmotion.LAUGHING,  # CosyVoice native alias
    "pause": SupportedEmotion.PAUSE,
    "sigh": SupportedEmotion.SAD,           # Paralinguistic sigh
    "breath": SupportedEmotion.WHISPER,     # Breath sound / soft whisper
    "quick_breath": SupportedEmotion.WHISPER,
}

# Emotion-specific acoustic & neural instruction configs
EMOTION_CONFIGS: dict[SupportedEmotion, dict] = {
    SupportedEmotion.HAPPY: {
        "instruction": "Speak with a cheerful, upbeat, and joyful tone<|endofprompt|>",
        "speed_multiplier": 1.05,
        "pitch_shift": 1.10,
    },
    SupportedEmotion.AMUSED: {
        "instruction": "Speak with a playful, amused, and smiling undertone<|endofprompt|>",
        "speed_multiplier": 1.02,
        "pitch_shift": 1.05,
    },
    SupportedEmotion.EXCITED: {
        "instruction": "Speak fast with high energy, enthusiasm, and vivid excitement<|endofprompt|>",
        "speed_multiplier": 1.15,
        "pitch_shift": 1.15,
    },
    SupportedEmotion.SAD: {
        "instruction": "Speak in a somber, melancholic, low-energy, and sorrowful voice<|endofprompt|>",
        "speed_multiplier": 0.88,
        "pitch_shift": 0.85,
    },
    SupportedEmotion.ANGRY: {
        "instruction": "Speak firmly with tense, sharp, aggressive, and forceful articulation<|endofprompt|>",
        "speed_multiplier": 1.08,
        "pitch_shift": 0.95,
    },
    SupportedEmotion.WHISPER: {
        "instruction": "Speak in a quiet, soft, breathy whisper<|endofprompt|>",
        "speed_multiplier": 0.92,
        "pitch_shift": 0.80,
    },
    SupportedEmotion.LAUGHING: {
        "instruction": "Speak with audible laughter and a bubbling, chuckling cadence<|endofprompt|>",
        "speed_multiplier": 1.05,
        "pitch_shift": 1.08,
    },
    SupportedEmotion.NEUTRAL: {
        "instruction": "Speak in a natural, balanced, clear conversational tone<|endofprompt|>",
        "speed_multiplier": 1.0,
        "pitch_shift": 1.0,
    },
    SupportedEmotion.PAUSE: {
        "instruction": "Insert acoustic silence<|endofprompt|>",
        "speed_multiplier": 1.0,
        "pitch_shift": 1.0,
    },
}

def clean_normalized_text(text: str) -> str:
    """
    Remove all bracketed tags and normalize spacing without corrupting punctuation.
    Preserves commas, periods, exclamation points, question marks, semicolons, and quotes.
    """
    if not text:
        return ""
    # 1. Strip all bracketed control tags
    stripped = TAG_PATTERN.sub("", text)
    # 2. Fix rogue spaces immediately preceding punctuation marks
    stripped = re.sub(r"\s+([,.\?!;:…])", r"\1", stripped)
    # 3. Collapse multiple whitespace characters into single space
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.strip()

def strip_emotion_tags(raw_text: str) -> str:
    """Convenience helper to strip all emotion/prosody tags from a string."""
    return clean_normalized_text(raw_text)

def has_emotion_tags(raw_text: str) -> bool:
    """Return True if the text contains any bracketed emotion or control tags."""
    if not raw_text:
        return False
    return bool(TAG_PATTERN.search(raw_text))

def verify_no_tags_in_text(text: str) -> bool:
    """
    Invariant check: returns True if NO bracketed control tags remain in the text.
    Ensures control tags are never sent to the acoustic phonemizer.
    """
    if not text:
        return True
    return not bool(TAG_PATTERN.search(text))

def _build_segment(text: str, emotion: SupportedEmotion, pause_ms: int = 0) -> EmotionSegment:
    """Construct an EmotionSegment enriched with instruction and prosody tuning parameters."""
    cfg = EMOTION_CONFIGS.get(emotion, EMOTION_CONFIGS[SupportedEmotion.NEUTRAL])
    return EmotionSegment(
        text=text,
        emotion=emotion,
        instruction=cfg.get("instruction"),
        speed_multiplier=cfg.get("speed_multiplier", 1.0),
        pitch_shift=cfg.get("pitch_shift", 1.0),
        pause_ms=pause_ms,
    )

def parse_emotion_text(raw_text: str) -> ParsedSpeech:
    """
    Parse text containing emotion and prosody tags into structured speech segments.

    Rules & Invariants:
    1. Emotion tags ([happy], [whisper], etc.) set the active emotion for subsequent text.
    2. Tags are strictly stripped and NEVER included in spoken text or segments.
    3. [pause] or [pause:ms] injects calibrated silence (default 500ms) after the preceding segment.
    4. Unknown tags (e.g. [curious], [robot]) are safely filtered out without errors.
    5. Spacing around punctuation marks is cleanly normalized.
    """
    if not raw_text or not raw_text.strip():
        return ParsedSpeech(
            raw_text=raw_text or "",
            clean_text="",
            leading_pause_ms=0,
            segments=[],
        )

    clean_text = clean_normalized_text(raw_text)

    # If all content was tags or whitespace, return empty clean_text
    if not clean_text:
        return ParsedSpeech(
            raw_text=raw_text,
            clean_text="",
            leading_pause_ms=0,
            segments=[],
        )

    segments: list[EmotionSegment] = []
    current_emotion = SupportedEmotion.NEUTRAL
    leading_pause_ms = 0
    last_idx = 0

    for match in TAG_PATTERN.finditer(raw_text):
        tag_name = match.group(1).lower()
        param_val = match.group(2)
        start, end = match.span()

        # Text chunk before this tag
        chunk = raw_text[last_idx:start]
        clean_chunk = clean_normalized_text(chunk)

        if clean_chunk:
            segments.append(_build_segment(clean_chunk, current_emotion, pause_ms=0))

        # Handle tag
        if tag_name in VALID_EMOTIONS:
            target_emotion = VALID_EMOTIONS[tag_name]
            if target_emotion == SupportedEmotion.PAUSE:
                # Determine pause duration (default 500ms, clamped between 50ms and 5000ms)
                pause_duration = 500
                if param_val:
                    try:
                        pause_duration = max(50, min(5000, int(param_val)))
                    except ValueError:
                        pause_duration = 500

                if segments:
                    segments[-1].pause_ms += pause_duration
                else:
                    leading_pause_ms += pause_duration
            else:
                current_emotion = target_emotion
        # Unknown tags are ignored here and will simply be stripped from text

        last_idx = end

    # Remaining text chunk after the final tag
    remainder = raw_text[last_idx:]
    clean_remainder = clean_normalized_text(remainder)
    if clean_remainder:
        segments.append(_build_segment(clean_remainder, current_emotion, pause_ms=0))

    # Fallback if no segments were created but clean_text exists
    if not segments and clean_text:
        segments.append(_build_segment(clean_text, SupportedEmotion.NEUTRAL, pause_ms=0))

    return ParsedSpeech(
        raw_text=raw_text,
        clean_text=clean_text,
        leading_pause_ms=leading_pause_ms,
        segments=segments,
    )
