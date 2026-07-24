"""Shared response schemas."""

from pydantic import BaseModel, Field


class ApiResponse[T](BaseModel):
    """Standard successful API envelope."""

    success: bool = True
    message: str
    data: T


class ErrorDetail(BaseModel):
    """Machine-readable error detail."""

    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error API envelope."""

    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)
