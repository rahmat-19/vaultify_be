"""Authentication application service."""

import hmac
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.security.passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.security.tokens import TokenService


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuthService:
    """Account, login, and session lifecycle use cases."""

    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        tokens: TokenService,
        settings: Settings,
    ) -> None:
        self.users = users
        self.refresh_tokens = refresh_tokens
        self.tokens = tokens
        self.settings = settings

    def register(self, payload: RegisterRequest) -> User:
        if self.users.get_by_email(str(payload.email)):
            raise ConflictError("An account with this email already exists")
        return self.users.create(
            payload.fullname, str(payload.email), hash_password(payload.password)
        )

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(str(payload.email))
        if user is None:
            # Equalize much of the hashing work for unknown accounts.
            verify_password(payload.password, DUMMY_PASSWORD_HASH)
            raise AuthenticationError()
        now = datetime.now(UTC)
        if user.locked_until and _as_utc(user.locked_until) > now:
            raise AuthenticationError("Account is temporarily locked")
        if not verify_password(payload.password, user.password_hash):
            attempts = user.failed_login_attempts + 1
            locked_until = None
            if attempts >= 5:
                locked_until = now + timedelta(
                    minutes=self.settings.account_lock_minutes
                )
                attempts = 0
            self.users.record_failed_login(user, attempts, locked_until)
            raise AuthenticationError()
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        self.users.reset_failed_logins(user)
        return self._issue_session(user)

    def refresh(self, raw_token: str) -> TokenResponse:
        digest = self.tokens.hash_refresh_token(raw_token)
        stored = self.refresh_tokens.get_active(digest)
        now = datetime.now(UTC)
        if stored is None or _as_utc(stored.expires_at) <= now:
            raise AuthenticationError("Invalid or expired refresh token")
        user = self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid session")
        self.refresh_tokens.revoke(stored)
        return self._issue_session(user)

    def logout(self, raw_token: str, current_user: User) -> None:
        digest = self.tokens.hash_refresh_token(raw_token)
        stored = self.refresh_tokens.get_active(digest)
        if (
            stored
            and stored.user_id == current_user.id
            and hmac.compare_digest(stored.token_hash, digest)
        ):
            self.refresh_tokens.revoke(stored)

    def _issue_session(self, user: User) -> TokenResponse:
        access_token, expires_in = self.tokens.create_access_token(user.id)
        refresh_token = self.tokens.create_refresh_token()
        self.refresh_tokens.create(
            user.id,
            self.tokens.hash_refresh_token(refresh_token),
            datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days),
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
