"""Logging setup helpers for note_writer_app."""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
from pathlib import Path


class _JSONFormatter(logging.Formatter):
    """Format app logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": os.environ.get("SERVICE_NAME", "unknown"),
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            data["traceback"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


class _BenignNiceGUIErrorFilter(logging.Filter):
    """Suppress noisy framework disconnect errors that are not actionable."""

    _DROP_PATTERNS = (
        "The parent slot of the element has been deleted.",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            message = ""
        if any(pattern in message for pattern in self._DROP_PATTERNS):
            return False
        if record.exc_info and record.exc_info[1] is not None:
            exc_text = str(record.exc_info[1])
            if any(pattern in exc_text for pattern in self._DROP_PATTERNS):
                return False
        return True


def setup_app_logging(log_dir: Path | str = "logs") -> None:
    """Configure the app rotating JSON log handler once."""
    normalized_log_dir = Path(log_dir)
    normalized_log_dir.mkdir(exist_ok=True)

    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler) and getattr(handler, "_techie_log", False):
            return

    handler = logging.handlers.RotatingFileHandler(
        normalized_log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(_JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    handler.addFilter(_BenignNiceGUIErrorFilter())
    handler._techie_log = True

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root.setLevel(level)
    root.addHandler(handler)

    logging.info("アプリ起動 (LOG_LEVEL=%s)", level_name)
