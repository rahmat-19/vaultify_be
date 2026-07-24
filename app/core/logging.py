"""Safe application logging configuration."""

import logging
from collections.abc import Mapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class SensitiveDataFilter(logging.Filter):
    """Redact common secret-bearing values from log records."""

    SENSITIVE_TERMS = {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "secret",
        "secure_note",
        "secure_notes",
        "api_key",
        "encryption_key",
    }

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        """Redact values stored under sensitive mapping keys."""
        if isinstance(value, Mapping):
            return {
                key: (
                    "[REDACTED]"
                    if str(key).lower() in cls.SENSITIVE_TERMS
                    else cls._sanitize(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(cls._sanitize(item) for item in value)
        if isinstance(value, list):
            return [cls._sanitize(item) for item in value]
        return value

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._sanitize(record.msg)
        if record.args:
            record.args = self._sanitize(record.args)
        return True


def configure_logging(
    level: str,
    log_file: str = "logs/app.log",
    max_bytes: int = 5_242_880,
    backup_count: int = 5,
) -> None:
    """Configure secret-safe console and rotating file logs."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    sensitive_filter = SensitiveDataFilter()

    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)
    else:
        for handler in root_logger.handlers:
            handler.addFilter(sensitive_filter)

    file_path = Path(log_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_file = file_path.resolve()
    already_configured = any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename).resolve() == resolved_file
        for handler in root_logger.handlers
    )
    if not already_configured:
        file_handler = RotatingFileHandler(
            resolved_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
