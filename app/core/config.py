"""Application configuration."""

from functools import lru_cache
from typing import Annotated

from pydantic import BeforeValidator, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_csv(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def _parse_debug(value: object) -> object:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"release", "production"}:
            return False
        if normalized in {"debug", "development"}:
            return True
    return value


StringList = Annotated[list[str], NoDecode, BeforeValidator(_split_csv)]
DebugFlag = Annotated[bool, BeforeValidator(_parse_debug)]


class Settings(BaseSettings):
    """Environment-backed settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Vaultify"
    environment: str = "development"
    debug: DebugFlag = False
    database_url: str = "sqlite:///./vaultify.db"
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=365)
    encryption_key: str
    cors_origins: StringList = ["*"]
    allowed_hosts: StringList = ["*"]
    # allowed_hosts: StringList = ["localhost", "127.0.0.1", "testserver"]
    rate_limit_default: str = "100/minute"
    rate_limit_login: str = "5/minute"
    account_lock_minutes: int = Field(default=15, ge=1, le=1440)
    log_level: str = "INFO"

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        """Ensure the key is URL-safe base64 encoding of exactly 32 bytes."""
        from app.security.encryption import decode_key

        decode_key(value)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()  # type: ignore[call-arg]
