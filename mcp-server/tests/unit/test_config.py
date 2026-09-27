from app.config import Settings

def test_settings_defaults():
    s = Settings()
    assert s.MCP_PORT == 3001
    assert s.DEFAULT_VOICE_ID == "1"
    assert s.MAX_TEXT_LENGTH == 5000
    assert s.DEFAULT_AUDIO_FORMAT == "wav"
    assert s.AUDIO_RETENTION_ENABLED is False
