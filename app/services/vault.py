"""Vault application service."""

import uuid

from app.core.audit import AuditTrail
from app.core.exceptions import NotFoundError
from app.models.vault_item import VaultItem
from app.repositories.vault import VaultRepository
from app.schemas.vault import VaultCreate, VaultResponse, VaultUpdate
from app.security.encryption import EncryptionService


class VaultService:
    """Ownership-safe vault use cases."""

    def __init__(
        self,
        repository: VaultRepository,
        encryption: EncryptionService,
        audit: AuditTrail,
    ) -> None:
        self.repository = repository
        self.encryption = encryption
        self.audit = audit

    def list_items(self, owner_id: uuid.UUID) -> list[VaultResponse]:
        result = [
            self._to_response(item) for item in self.repository.list_for_owner(owner_id)
        ]
        self.audit.record("vault.list", "success", actor=owner_id)
        return result

    def get(self, item_id: uuid.UUID, owner_id: uuid.UUID) -> VaultResponse:
        result = self._to_response(self._get_owned(item_id, owner_id))
        self.audit.record("vault.read", "success", actor=owner_id, resource=item_id)
        return result

    def create(self, payload: VaultCreate, owner_id: uuid.UUID) -> VaultResponse:
        item = VaultItem(
            owner_id=owner_id,
            title=payload.title,
            username=payload.username,
            encrypted_password=self.encryption.encrypt(payload.password),
            encrypted_notes=self.encryption.encrypt(payload.notes),
            website=str(payload.website) if payload.website else None,
            category=payload.category,
        )
        saved = self.repository.create(item)
        self.audit.record("vault.create", "success", actor=owner_id, resource=saved.id)
        return self._to_response(saved)

    def update(
        self, item_id: uuid.UUID, payload: VaultUpdate, owner_id: uuid.UUID
    ) -> VaultResponse:
        item = self._get_owned(item_id, owner_id)
        changes = payload.model_dump(exclude_unset=True)
        if "password" in changes:
            item.encrypted_password = self.encryption.encrypt(changes.pop("password"))
        if "notes" in changes:
            item.encrypted_notes = self.encryption.encrypt(changes.pop("notes"))
        if "website" in changes:
            website = changes.pop("website")
            item.website = str(website) if website else None
        for field, value in changes.items():
            setattr(item, field, value)
        saved = self.repository.save(item)
        self.audit.record("vault.update", "success", actor=owner_id, resource=item_id)
        return self._to_response(saved)

    def delete(self, item_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        self.repository.delete(self._get_owned(item_id, owner_id))
        self.audit.record("vault.delete", "success", actor=owner_id, resource=item_id)

    def search(self, owner_id: uuid.UUID, term: str) -> list[VaultResponse]:
        result = [
            self._to_response(item) for item in self.repository.search(owner_id, term)
        ]
        self.audit.record("vault.search", "success", actor=owner_id)
        return result

    def _get_owned(self, item_id: uuid.UUID, owner_id: uuid.UUID) -> VaultItem:
        item = self.repository.get_for_owner(item_id, owner_id)
        if item is None:
            # A 404 prevents disclosing whether another user owns the UUID.
            raise NotFoundError("Vault item not found")
        return item

    def _to_response(self, item: VaultItem) -> VaultResponse:
        return VaultResponse(
            id=item.id,
            title=item.title,
            username=item.username,
            password=self.encryption.decrypt(item.encrypted_password),
            notes=self.encryption.decrypt(item.encrypted_notes),
            website=item.website,
            category=item.category,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
