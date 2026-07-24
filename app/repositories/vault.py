"""Vault item persistence repository."""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.vault_item import VaultItem


class VaultRepository:
    """Ownership-scoped vault data access."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_owner(self, owner_id: uuid.UUID) -> list[VaultItem]:
        query = (
            select(VaultItem)
            .where(VaultItem.owner_id == owner_id)
            .order_by(VaultItem.updated_at.desc())
        )
        return list(self.db.scalars(query))

    def get_for_owner(
        self, item_id: uuid.UUID, owner_id: uuid.UUID
    ) -> VaultItem | None:
        return self.db.scalar(
            select(VaultItem).where(
                VaultItem.id == item_id, VaultItem.owner_id == owner_id
            )
        )

    def search(self, owner_id: uuid.UUID, term: str) -> list[VaultItem]:
        pattern = f"%{term.lower()}%"
        query = (
            select(VaultItem)
            .where(
                VaultItem.owner_id == owner_id,
                or_(
                    VaultItem.title.ilike(pattern),
                    VaultItem.username.ilike(pattern),
                    VaultItem.website.ilike(pattern),
                    VaultItem.category.ilike(pattern),
                ),
            )
            .order_by(VaultItem.updated_at.desc())
        )
        return list(self.db.scalars(query))

    def create(self, item: VaultItem) -> VaultItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def save(self, item: VaultItem) -> VaultItem:
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: VaultItem) -> None:
        self.db.delete(item)
        self.db.commit()
