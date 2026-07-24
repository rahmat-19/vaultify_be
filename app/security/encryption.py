"""AES-256-GCM field encryption."""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def decode_key(encoded_key: str) -> bytes:
    """Decode and validate a URL-safe base64 AES-256 key."""
    try:
        padded_key = encoded_key + ("=" * (-len(encoded_key) % 4))
        key = base64.b64decode(padded_key.encode(), altchars=b"-_", validate=True)
    except Exception as exc:
        raise ValueError("ENCRYPTION_KEY must be URL-safe base64") from exc
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


class EncryptionService:
    """Authenticated encryption for sensitive vault fields."""

    VERSION = "v1"

    def __init__(self, encoded_key: str) -> None:
        self._cipher = AESGCM(decode_key(encoded_key))

    def encrypt(self, plaintext: str | None) -> str | None:
        """Encrypt text with a fresh 96-bit nonce."""
        if plaintext is None:
            return None
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(nonce, plaintext.encode(), None)
        payload = base64.urlsafe_b64encode(nonce + ciphertext).decode()
        return f"{self.VERSION}:{payload}"

    def decrypt(self, payload: str | None) -> str | None:
        """Decrypt and authenticate a versioned ciphertext."""
        if payload is None:
            return None
        version, separator, encoded = payload.partition(":")
        if not separator or version != self.VERSION:
            raise ValueError("Unsupported encrypted payload")
        raw = base64.urlsafe_b64decode(encoded.encode())
        if len(raw) < 29:
            raise ValueError("Invalid encrypted payload")
        return self._cipher.decrypt(raw[:12], raw[12:], None).decode()
