"""Authentication request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.security.passwords import validate_password_strength
from app.utils.sanitization import normalize_display_text


class RegisterRequest(BaseModel):
    """New account payload."""

    fullname: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str

    _password_policy = field_validator("password")(validate_password_strength)

    @field_validator("fullname")
    @classmethod
    def clean_fullname(cls, value: str) -> str:
        return normalize_display_text(value)  # type: ignore[return-value]


class LoginRequest(BaseModel):
    """Credential login payload."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class RefreshRequest(BaseModel):
    """Refresh-token rotation payload."""

    refresh_token: str = Field(min_length=40, max_length=512)


class LogoutRequest(RefreshRequest):
    """Session logout payload."""


class UserResponse(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fullname: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Issued access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
