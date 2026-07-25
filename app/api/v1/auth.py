"""Authentication routes."""

from fastapi import APIRouter, Request, status

from app.api.dependencies import AuthServiceDep, CurrentUser
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def register(
    request: Request, payload: RegisterRequest, service: AuthServiceDep
) -> ApiResponse[UserResponse]:
    """Create a user account."""
    user = service.register(payload)
    return ApiResponse(
        message="Account created successfully", data=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
@limiter.limit(get_settings().rate_limit_login)
def login(
    request: Request, payload: LoginRequest, service: AuthServiceDep
) -> ApiResponse[TokenResponse]:
    """Authenticate and create a new session."""
    return ApiResponse(message="Login successful", data=service.login(payload))


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
@limiter.limit("10/minute")
def refresh(
    request: Request, payload: RefreshRequest, service: AuthServiceDep
) -> ApiResponse[TokenResponse]:
    """Rotate a refresh token and issue a new access token."""
    return ApiResponse(
        message="Token refreshed", data=service.refresh(payload.refresh_token)
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(  
    payload: LogoutRequest, current_user: CurrentUser, service: AuthServiceDep
) -> ApiResponse[dict]:
    """Revoke the supplied current-user refresh token."""
    service.logout(payload.refresh_token, current_user)
    return ApiResponse(message="Logout successful", data={})


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(current_user: CurrentUser) -> ApiResponse[UserResponse]:
    """Return the authenticated user."""
    return ApiResponse(
        message="User retrieved",
        data=UserResponse.model_validate(current_user),
    )
