"""Vault item schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.utils.sanitization import normalize_display_text, reject_null_bytes


class VaultBase(BaseModel):
    """Validated vault fields."""

    title: str = Field(min_length=1, max_length=200)
    username: str | None = Field(default=None, max_length=320)
    password: str | None = Field(default=None, max_length=10_000)
    notes: str | None = Field(default=None, max_length=50_000)
    website: HttpUrl | None = None
    category: str = Field(default="login", min_length=1, max_length=50)

    @field_validator("title", "username", "category")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return normalize_display_text(value)

    _safe_sensitive_text = field_validator("password", "notes")(reject_null_bytes)


class VaultCreate(VaultBase):
    """Create vault item payload."""


class VaultUpdate(BaseModel):
    """Partial vault update payload."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    username: str | None = Field(default=None, max_length=320)
    password: str | None = Field(default=None, max_length=10_000)
    notes: str | None = Field(default=None, max_length=50_000)
    website: HttpUrl | None = None
    category: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("title", "username", "category")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return VaultBase.clean_text(value)

    _safe_sensitive_text = field_validator("password", "notes")(reject_null_bytes)


class VaultResponse(BaseModel):
    """Decrypted vault item returned only to its owner."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    username: str | None
    password: str | None
    notes: str | None
    website: str | None
    category: str
    created_at: datetime
    updated_at: datetime
