import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            data["request_id"] = record.request_id
        if hasattr(record, "metrics"):
            data["metrics"] = record.metrics
        if hasattr(record, "extra_data"):
            data["extra_data"] = record.extra_data
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)

def setup_logger(name: str = "echomcp", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger

logger = setup_logger()
