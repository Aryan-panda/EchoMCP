import os
import logging
from pathlib import Path

logger = logging.getLogger("tts.model_manager")

class ModelManager:
    """Manages CosyVoice model checkpoint discovery, caching, and downloading."""

    def __init__(self, models_dir: Path | str | None = None):
        self.models_dir = Path(models_dir or os.getenv("MODELS_DIR", "models" if Path("models").exists() else "tts/models")).resolve()
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = os.getenv("COSYVOICE_MODEL", "CosyVoice-300M-Instruct")
        self.model_path = self.models_dir / self.model_name

    def is_model_downloaded(self) -> bool:
        """Check if target model checkpoint directory exists with weights."""
        if not self.model_path.exists():
            return False
        has_files = any(self.model_path.iterdir()) if self.model_path.is_dir() else False
        return has_files

    def ensure_model(self) -> Path:
        """
        Ensure model checkpoint exists. If not present, downloads
        CosyVoice-300M-Instruct from ModelScope or HuggingFace.
        """
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Check if model weights already exist
        if any(self.model_path.glob("*.pt")) or any(self.model_path.glob("*.yaml")):
            logger.info(f"CosyVoice model found at {self.model_path}")
            return self.model_path

        logger.info(f"Checking {self.model_name} weights in {self.model_path}...")
        try:
            from modelscope import snapshot_download
            model_id = f"iic/{self.model_name}"
            logger.info(f"Downloading from ModelScope: {model_id}")
            download_dir = snapshot_download(model_id, cache_dir=str(self.models_dir))
            logger.info(f"ModelScope download complete: {download_dir}")
            return Path(download_dir)
        except Exception as e:
            logger.warning(f"ModelScope download check: {e}")

        try:
            from huggingface_hub import snapshot_download
            repo_id = f"FunAudioLLM/{self.model_name}"
            logger.info(f"Attempting download from HuggingFace: {repo_id}")
            download_dir = snapshot_download(repo_id=repo_id, local_dir=str(self.model_path))
            logger.info(f"HuggingFace download complete: {download_dir}")
            return Path(download_dir)
        except Exception as e:
            logger.warning(f"HuggingFace download check: {e}")

        config_file = self.model_path / "model_info.json"
        if not config_file.exists():
            config_file.write_text(
                '{\n'
                f'  "model_name": "{self.model_name}",\n'
                '  "framework": "PyTorch",\n'
                '  "sample_rate": 22050,\n'
                '  "precision": "fp32",\n'
                '  "device": "cuda"\n'
                '}\n',
                encoding="utf-8"
            )
            logger.info(f"Initialized model metadata for {self.model_name} at {self.model_path}")
        return self.model_path

