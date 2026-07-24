"""API v1 route aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, vault

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(vault.router)
