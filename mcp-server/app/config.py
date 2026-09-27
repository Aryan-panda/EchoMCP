import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    MCP_HOST: str = "0.0.0.0"
    MCP_PORT: int = 3001
    MCP_AUTH_TOKEN: str = "change-me"

    TTS_BASE_URL: str = "http://tts:8080"
    DEFAULT_VOICE_ID: str = "1"

    MAX_TEXT_LENGTH: int = 5000
    MAX_AUDIO_SECONDS: int = 120
    DEFAULT_AUDIO_FORMAT: str = "wav"
    DEFAULT_SPEED: float = 1.0

    AUDIO_RETENTION_ENABLED: bool = False
    AUDIO_RETENTION_DAYS: int = 30
    LOG_LEVEL: str = "INFO"

    STORAGE_VOICES_DIR: str = os.getenv("STORAGE_VOICES_DIR", "tts/voices")
    STORAGE_OUTPUT_DIR: str = os.getenv("STORAGE_OUTPUT_DIR", "tts/output")

    @property
    def voices_path(self) -> Path:
        return Path(self.STORAGE_VOICES_DIR).resolve()

    @property
    def output_path(self) -> Path:
        return Path(self.STORAGE_OUTPUT_DIR).resolve()

    @property
    def metadata_path(self) -> Path:
        return self.output_path / "metadata"

settings = Settings()
