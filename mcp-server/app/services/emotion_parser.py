import re
from app.models.speech import SupportedEmotion, EmotionSegment, ParsedSpeech

# Regex for tags like [happy], [amused], etc.
TAG_PATTERN = re.compile(r"\[([a-zA-Z]+)\]")

VALID_EMOTIONS = {
    "happy": SupportedEmotion.HAPPY,
    "amused": SupportedEmotion.AMUSED,
    "excited": SupportedEmotion.EXCITED,
    "sad": SupportedEmotion.SAD,
    "angry": SupportedEmotion.ANGRY,
    "whisper": SupportedEmotion.WHISPER,
    "laughing": SupportedEmotion.LAUGHING,
    "pause": SupportedEmotion.PAUSE,
}

def parse_emotion_text(raw_text: str) -> ParsedSpeech:
    """
    Parse text containing emotion tags into structured segments.
    Ensures that tags are completely stripped from spoken text.
    Handles unknown tags safely by stripping them.
    """
    if not raw_text or not raw_text.strip():
        return ParsedSpeech(
            raw_text=raw_text,
            clean_text="",
            segments=[]
        )

    # Clean text: remove all bracketed tags [tag]
    clean_text = TAG_PATTERN.sub("", raw_text)
    # Normalize excessive spaces while keeping punctuation and single spaces
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # Split into segments by emotion tags
    segments: list[EmotionSegment] = []
    current_emotion = SupportedEmotion.NEUTRAL
    last_idx = 0

    for match in TAG_PATTERN.finditer(raw_text):
        tag_text = match.group(1).lower()
        start, end = match.span()

        # Capture preceding text with the active emotion
        text_before = raw_text[last_idx:start]
        # Clean text snippet
        clean_snippet = TAG_PATTERN.sub("", text_before).strip()
        if clean_snippet:
            segments.append(
                EmotionSegment(
                    text=clean_snippet,
                    emotion=current_emotion,
                    pause_ms=0
                )
            )

        # Update active emotion if valid, otherwise keep previous
        if tag_text in VALID_EMOTIONS:
            if tag_text == "pause":
                # Pause tag inserts an acoustic silence pause
                if segments:
                    segments[-1].pause_ms = 500
            else:
                current_emotion = VALID_EMOTIONS[tag_text]

        last_idx = end

    # Remaining text after the final tag
    remainder = raw_text[last_idx:]
    clean_remainder = TAG_PATTERN.sub("", remainder).strip()
    if clean_remainder:
        segments.append(
            EmotionSegment(
                text=clean_remainder,
                emotion=current_emotion,
                pause_ms=0
            )
        )

    # Fallback if no segments were created (e.g. text was purely punctuation/spaces)
    if not segments and clean_text:
        segments.append(
            EmotionSegment(
                text=clean_text,
                emotion=SupportedEmotion.NEUTRAL,
                pause_ms=0
            )
        )

    return ParsedSpeech(
        raw_text=raw_text,
        clean_text=clean_text,
        segments=segments
    )
