"""JWT and opaque-token helpers."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import Settings
from app.core.exceptions import AuthenticationError


class TokenService:
    """Issue and validate short-lived access tokens."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_access_token(self, user_id: uuid.UUID) -> tuple[str, int]:
        """Create a signed JWT and return its lifetime in seconds."""
        lifetime = timedelta(minutes=self.settings.access_token_expire_minutes)
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + lifetime,
            "jti": str(uuid.uuid4()),
        }
        return (
            jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm,
            ),
            int(lifetime.total_seconds()),
        )

    def decode_access_token(self, token: str) -> uuid.UUID:
        """Validate an access JWT and return its user ID."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            if payload.get("type") != "access":
                raise AuthenticationError()
            return uuid.UUID(payload["sub"])
        except (JWTError, KeyError, ValueError) as exc:
            raise AuthenticationError("Invalid or expired access token") from exc

    @staticmethod
    def create_refresh_token() -> str:
        """Create a high-entropy opaque refresh token."""
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        """Return a deterministic one-way refresh-token digest."""
        return hashlib.sha256(token.encode()).hexdigest()
