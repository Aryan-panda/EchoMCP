import pytest
from app.models.speech import SupportedEmotion
from app.services.emotion_parser import (
    parse_emotion_text,
    strip_emotion_tags,
    has_emotion_tags,
    verify_no_tags_in_text,
    VALID_EMOTIONS,
    EMOTION_CONFIGS,
)

def test_controlled_tags_individual():
    """Verify each controlled vocabulary tag is correctly parsed and sets emotion."""
    tags_to_test = [
        ("[happy] Feeling wonderful today.", SupportedEmotion.HAPPY, "Feeling wonderful today."),
        ("[amused] That really made me chuckle.", SupportedEmotion.AMUSED, "That really made me chuckle."),
        ("[excited] We won the championship!", SupportedEmotion.EXCITED, "We won the championship!"),
        ("[sad] It is truly heartbreaking.", SupportedEmotion.SAD, "It is truly heartbreaking."),
        ("[angry] Stop doing that immediately!", SupportedEmotion.ANGRY, "Stop doing that immediately!"),
        ("[whisper] Keep your voice down.", SupportedEmotion.WHISPER, "Keep your voice down."),
        ("[laughing] That joke was incredible.", SupportedEmotion.LAUGHING, "That joke was incredible."),
    ]

    for raw, expected_emotion, expected_clean in tags_to_test:
        parsed = parse_emotion_text(raw)
        assert parsed.clean_text == expected_clean
        assert len(parsed.segments) == 1
        assert parsed.segments[0].emotion == expected_emotion
        assert parsed.segments[0].text == expected_clean
        assert verify_no_tags_in_text(parsed.clean_text)

def test_paralinguistic_aliases():
    """Verify CosyVoice paralinguistic aliases map to appropriate emotions."""
    # [laughter] alias for laughing
    parsed_laughter = parse_emotion_text("[laughter] That is too funny.")
    assert parsed_laughter.segments[0].emotion == SupportedEmotion.LAUGHING
    assert parsed_laughter.clean_text == "That is too funny."

    # [sigh] mapped to sad/resigned prosody
    parsed_sigh = parse_emotion_text("[sigh] Here we go again.")
    assert parsed_sigh.segments[0].emotion == SupportedEmotion.SAD
    assert parsed_sigh.clean_text == "Here we go again."

    # [breath] / [quick_breath] mapped to whisper
    parsed_breath = parse_emotion_text("[breath] Take a deep breath.")
    assert parsed_breath.segments[0].emotion == SupportedEmotion.WHISPER
    assert parsed_breath.clean_text == "Take a deep breath."

def test_tag_case_insensitivity():
    """Verify tags work identically regardless of uppercase/lowercase."""
    variations = [
        "[HAPPY] I am glad.",
        "[Happy] I am glad.",
        "[hApPy] I am glad.",
        "[WHISPER] Quiet please.",
        "[Excited] Let's go!",
    ]
    for raw in variations:
        parsed = parse_emotion_text(raw)
        assert verify_no_tags_in_text(parsed.clean_text)
        assert "[" not in parsed.clean_text
        assert "]" not in parsed.clean_text

def test_tags_never_spoken_invariant():
    """
    CRITICAL INVARIANT:
    Tags are NEVER included in clean_text or segment.text.
    Phonemizer must never receive literal tag words.
    """
    raw = "[excited] Look! [whisper] Did you hear that? [pause] [amused] Haha, nevermind."
    parsed = parse_emotion_text(raw)

    assert verify_no_tags_in_text(parsed.clean_text)
    assert "excited" not in parsed.clean_text.lower().split()
    assert "whisper" not in parsed.clean_text.lower().split()
    assert "pause" not in parsed.clean_text.lower().split()
    assert "amused" not in parsed.clean_text.lower().split()

    for seg in parsed.segments:
        assert verify_no_tags_in_text(seg.text)
        assert "[" not in seg.text
        assert "]" not in seg.text

def test_unknown_tags_stripped_gracefully():
    """Verify unknown or unlisted tags are stripped cleanly without errors or crashing."""
    raw = "This is [unknown] normal text [robot] with [custom_tag:123] random tags."
    parsed = parse_emotion_text(raw)
    assert parsed.clean_text == "This is normal text with random tags."
    assert verify_no_tags_in_text(parsed.clean_text)

def test_punctuation_preservation():
    """Verify commas, quotes, periods, exclamation, questions, ellipses are preserved cleanly."""
    raw = 'Wait... [whisper] "Are you sure?!" [pause] Yes, absolutely: 100% ready!'
    parsed = parse_emotion_text(raw)

    # Clean text should preserve all punctuation marks and normalize rogue spaces
    assert parsed.clean_text == 'Wait... "Are you sure?!" Yes, absolutely: 100% ready!'
    assert verify_no_tags_in_text(parsed.clean_text)

def test_multi_segment_emotion_transitions():
    """Verify multiple emotion tags split text into ordered segments with correct emotions."""
    raw = "[excited] We breached light speed! [pause] [whisper] Hold on tight."
    parsed = parse_emotion_text(raw)

    assert len(parsed.segments) == 2

    # Segment 1
    seg1 = parsed.segments[0]
    assert seg1.text == "We breached light speed!"
    assert seg1.emotion == SupportedEmotion.EXCITED
    assert seg1.pause_ms == 500  # Pause immediately follows segment 1

    # Segment 2
    seg2 = parsed.segments[1]
    assert seg2.text == "Hold on tight."
    assert seg2.emotion == SupportedEmotion.WHISPER
    assert seg2.pause_ms == 0

def test_pause_explicit_duration_and_accumulation():
    """Verify [pause] and [pause:ms] syntax, duration clamping, and pause accumulation."""
    # Explicit 800ms pause
    raw1 = "First sentence. [pause:800] Second sentence."
    parsed1 = parse_emotion_text(raw1)
    assert parsed1.segments[0].pause_ms == 800

    # Accumulated pauses: [pause] (500) + [pause:250] = 750ms
    raw2 = "Hold on. [pause] [pause:250] Moving forward."
    parsed2 = parse_emotion_text(raw2)
    assert parsed2.segments[0].pause_ms == 750

    # Leading pause before any text
    raw3 = "[pause:400] Starting after a short pause."
    parsed3 = parse_emotion_text(raw3)
    assert parsed3.leading_pause_ms == 400
    assert parsed3.segments[0].text == "Starting after a short pause."

    # Clamping extreme pause values (min 50ms, max 5000ms)
    raw_clamp_low = "A [pause:10] B"
    assert parse_emotion_text(raw_clamp_low).segments[0].pause_ms == 50

    raw_clamp_high = "A [pause:99999] B"
    assert parse_emotion_text(raw_clamp_high).segments[0].pause_ms == 5000

def test_empty_and_whitespace_input():
    """Verify graceful handling of empty or blank text."""
    for empty_input in ["", "   ", "\n\t  ", None]:
        parsed = parse_emotion_text(empty_input)
        assert parsed.clean_text == ""
        assert parsed.segments == []
        assert parsed.leading_pause_ms == 0

def test_only_tags_produces_empty_clean_text():
    """Verify input with only emotion/pause tags yields empty clean_text."""
    raw = "[happy] [whisper] [pause] [amused]"
    parsed = parse_emotion_text(raw)
    assert parsed.clean_text == ""
    assert parsed.segments == []

def test_plain_text_without_tags():
    """Verify plain text without any tags produces a single NEUTRAL segment."""
    raw = "Just a standard conversational sentence without any tags."
    parsed = parse_emotion_text(raw)
    assert parsed.clean_text == raw
    assert len(parsed.segments) == 1
    assert parsed.segments[0].emotion == SupportedEmotion.NEUTRAL
    assert parsed.segments[0].pause_ms == 0

def test_cosyvoice_instruction_and_prosody_multipliers():
    """Verify segments contain valid CosyVoice instruct prompts and prosody multipliers."""
    raw = "[excited] Full throttle! [sad] We ran out of fuel."
    parsed = parse_emotion_text(raw)

    seg_excited = parsed.segments[0]
    assert "<|endofprompt|>" in seg_excited.instruction
    assert "excited" in seg_excited.instruction.lower() or "excitement" in seg_excited.instruction.lower()
    assert seg_excited.speed_multiplier > 1.0
    assert seg_excited.pitch_shift > 1.0

    seg_sad = parsed.segments[1]
    assert "<|endofprompt|>" in seg_sad.instruction
    assert "somber" in seg_sad.instruction.lower() or "sorrowful" in seg_sad.instruction.lower()
    assert seg_sad.speed_multiplier < 1.0
    assert seg_sad.pitch_shift < 1.0

def test_strip_and_has_emotion_tags_helpers():
    """Verify standalone convenience helpers."""
    assert has_emotion_tags("[happy] Hello") is True
    assert has_emotion_tags("Plain text") is False
    assert strip_emotion_tags("[excited] Incredible! [pause]") == "Incredible!"
