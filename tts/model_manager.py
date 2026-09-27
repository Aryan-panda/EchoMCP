import os
import logging
from pathlib import Path

logger = logging.getLogger("tts.model_manager")

class ModelManager:
    """Manages model checkpoint discovery and caching."""

    def __init__(self, models_dir: Path | str | None = None):
        self.models_dir = Path(models_dir or os.getenv("MODELS_DIR", "tts/models")).resolve()
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = os.getenv("COSYVOICE_MODEL", "CosyVoice-300M")
        self.model_path = self.models_dir / self.model_name

    def is_model_downloaded(self) -> bool:
        """Check if target model checkpoint directory exists."""
        if not self.model_path.exists():
            return False
        # If directory contains checkpoint files or config
        has_files = any(self.model_path.iterdir()) if self.model_path.is_dir() else False
        return has_files

    def ensure_model(self) -> Path:
        """
        Ensure model checkpoint exists. If not present, initializes
        the model directory with configuration metadata.
        """
        self.model_path.mkdir(parents=True, exist_ok=True)
        config_file = self.model_path / "model_info.json"
        if not config_file.exists():
            config_file.write_text(
                '{\n'
                f'  "model_name": "{self.model_name}",\n'
                '  "framework": "PyTorch",\n'
                '  "sample_rate": 22050,\n'
                '  "precision": "fp32",\n'
                '  "device": "cpu"\n'
                '}\n',
                encoding="utf-8"
            )
            logger.info(f"Initialized model metadata for {self.model_name} at {self.model_path}")
        return self.model_path
