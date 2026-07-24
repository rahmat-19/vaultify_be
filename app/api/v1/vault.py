"""Vault item routes."""

import uuid

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser, VaultServiceDep
from app.schemas.common import ApiResponse
from app.schemas.vault import VaultCreate, VaultResponse, VaultUpdate

router = APIRouter(prefix="/vault", tags=["Vault"])


@router.get("", response_model=ApiResponse[list[VaultResponse]])
def list_vault(
    current_user: CurrentUser, service: VaultServiceDep
) -> ApiResponse[list[VaultResponse]]:
    """List only the current user's items."""
    return ApiResponse(
        message="Vault items retrieved", data=service.list_items(current_user.id)
    )


@router.get("/search", response_model=ApiResponse[list[VaultResponse]])
def search_vault(
    current_user: CurrentUser,
    service: VaultServiceDep,
    q: str = Query(min_length=1, max_length=200),
) -> ApiResponse[list[VaultResponse]]:
    """Search non-sensitive metadata in the current user's vault."""
    return ApiResponse(
        message="Search complete", data=service.search(current_user.id, q.strip())
    )


@router.get("/{item_id}", response_model=ApiResponse[VaultResponse])
def get_vault(
    item_id: uuid.UUID, current_user: CurrentUser, service: VaultServiceDep
) -> ApiResponse[VaultResponse]:
    """Retrieve and decrypt one owned item."""
    return ApiResponse(
        message="Vault item retrieved", data=service.get(item_id, current_user.id)
    )


@router.post(
    "",
    response_model=ApiResponse[VaultResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_vault(
    payload: VaultCreate, current_user: CurrentUser, service: VaultServiceDep
) -> ApiResponse[VaultResponse]:
    """Encrypt and create a vault item."""
    return ApiResponse(
        message="Vault item created",
        data=service.create(payload, current_user.id),
    )


@router.put("/{item_id}", response_model=ApiResponse[VaultResponse])
def update_vault(
    item_id: uuid.UUID,
    payload: VaultUpdate,
    current_user: CurrentUser,
    service: VaultServiceDep,
) -> ApiResponse[VaultResponse]:
    """Update an owned vault item."""
    return ApiResponse(
        message="Vault item updated",
        data=service.update(item_id, payload, current_user.id),
    )


@router.delete("/{item_id}", response_model=ApiResponse[dict])
def delete_vault(
    item_id: uuid.UUID, current_user: CurrentUser, service: VaultServiceDep
) -> ApiResponse[dict]:
    """Delete an owned vault item."""
    service.delete(item_id, current_user.id)
    return ApiResponse(message="Vault item deleted", data={})
