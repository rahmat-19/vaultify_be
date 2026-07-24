"""Vaultify FastAPI entry point."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.middleware.security import SecurityHeadersMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vaultify - Secure Password Vault",
    version="1.0.0",
    debug=settings.debug,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Serialize expected errors without internal details."""
    logger.warning(
        "Application error method=%s path=%s status=%s message=%s errors=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.message,
        exc.errors,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "errors": exc.errors},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize framework HTTP errors."""
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    logger.warning(
        "HTTP error method=%s path=%s status=%s message=%s",
        request.method,
        request.url.path,
        exc.status_code,
        message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": message, "errors": []},
        headers=exc.headers,
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return rate-limit failures in the standard envelope."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Rate limit exceeded",
            "errors": [],
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Serialize Pydantic validation errors in the standard envelope."""
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or None,
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    logger.warning(
        "Request validation failed method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        errors,
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Request validation failed",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures and return a generic response."""
    logger.exception("Unhandled application error")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal error occurred",
            "errors": [],
        },
    )


@app.get("/health", tags=["Health"])
def health() -> dict:
    """Liveness endpoint."""
    return {"success": True, "message": "Vaultify is healthy", "data": {}}


app.include_router(api_router)
