"""Privacy-preserving security audit trail."""

import hashlib
import hmac
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.logging import SensitiveDataFilter

AUDIT_LOGGER_NAME = "vaultify.audit"


def configure_audit_logging(
    log_file: str,
    max_bytes: int = 5_242_880,
    backup_count: int = 5,
) -> None:
    """Write audit events to a dedicated rotating file."""
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    file_path = Path(log_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_file = file_path.resolve()
    if any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename).resolve() == resolved_file
        for handler in logger.handlers
    ):
        return

    handler = RotatingFileHandler(
        resolved_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.addFilter(SensitiveDataFilter())
    logger.addHandler(handler)


class AuditTrail:
    """Record correlatable events without storing direct user identifiers."""

    def __init__(self, fingerprint_key: str) -> None:
        self._key = fingerprint_key.encode()
        self._logger = logging.getLogger(AUDIT_LOGGER_NAME)

    def _fingerprint(self, value: object | None) -> str:
        if value is None:
            return "anonymous"
        return hmac.new(
            self._key,
            str(value).strip().lower().encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

    def record(
        self,
        event: str,
        outcome: str,
        *,
        actor: object | None = None,
        resource: object | None = None,
    ) -> None:
        """Write a fixed-field, single-line audit event."""
        self._logger.info(
            "event=%s outcome=%s actor=%s resource=%s",
            event,
            outcome,
            self._fingerprint(actor),
            self._fingerprint(resource) if resource is not None else "-",
        )
