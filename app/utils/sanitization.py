"""Conservative text normalization for display metadata."""

import unicodedata


def normalize_display_text(value: str | None) -> str | None:
    """Trim whitespace and reject invisible control characters."""
    if value is None:
        return None
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise ValueError("Control characters are not allowed")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError("Value cannot be blank")
    return cleaned


def reject_null_bytes(value: str | None) -> str | None:
    """Reject null bytes while preserving secret/note contents exactly."""
    if value is not None and "\x00" in value:
        raise ValueError("Null bytes are not allowed")
    return value
