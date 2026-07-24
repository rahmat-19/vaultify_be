"""FastAPI dependency wiring."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.database.session import get_db
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.repositories.vault import VaultRepository
from app.security.encryption import EncryptionService
from app.security.tokens import TokenService
from app.services.auth import AuthService
from app.services.vault import VaultService

bearer = HTTPBearer(auto_error=False)
DbDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_token_service(settings: SettingsDep) -> TokenService:
    return TokenService(settings)


def get_auth_service(
    db: DbDep,
    settings: SettingsDep,
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> AuthService:
    return AuthService(UserRepository(db), RefreshTokenRepository(db), tokens, settings)


def get_vault_service(db: DbDep, settings: SettingsDep) -> VaultService:
    return VaultService(VaultRepository(db), EncryptionService(settings.encryption_key))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DbDep,
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    """Authenticate and load the active user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Authentication required")
    user_id = tokens.decode_access_token(credentials.credentials)
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid session")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
VaultServiceDep = Annotated[VaultService, Depends(get_vault_service)]
