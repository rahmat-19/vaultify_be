"""Safe application logging configuration."""

import logging


class SensitiveDataFilter(logging.Filter):
    """Redact common secret-bearing values from log records."""

    SENSITIVE_TERMS = {
        "password",
        "token",
        "authorization",
        "secret",
        "api_key",
        "encryption_key",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, dict):
            record.msg = {
                key: "[REDACTED]" if key.lower() in self.SENSITIVE_TERMS else value
                for key, value in record.msg.items()
            }
        return True


def configure_logging(level: str) -> None:
    """Configure structured-enough, secret-safe console logs."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(SensitiveDataFilter())
