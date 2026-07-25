"""Seed a dummy user for local development.

Revision ID: 0002_seed_dummy_user
Revises: ee86a1adbe04
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "0002_seed_dummy_user"
down_revision: str | None = "ee86a1adbe04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DUMMY_USER_ID = uuid.UUID("d7c090d5-cc95-4f14-9107-ec96309021b9")
DUMMY_USER_EMAIL = "dummy@example.com"

users = sa.table(
    "users",
    sa.column("id", sa.Uuid()),
    sa.column("fullname", sa.String()),
    sa.column("email", sa.String()),
    sa.column("password_hash", sa.String()),
    sa.column("is_active", sa.Boolean()),
    sa.column("failed_login_attempts", sa.Integer()),
    sa.column("locked_until", sa.DateTime(timezone=True)),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    """Insert the development-only dummy user."""
    seeded_at = datetime(2026, 7, 25, tzinfo=UTC)
    op.bulk_insert(
        users,
        [
            {
                "id": DUMMY_USER_ID,
                "fullname": "Dummy User",
                "email": DUMMY_USER_EMAIL,
                "password_hash": (
                    "$argon2id$v=19$m=65536,t=3,p=4$"
                    "Fk6OfblJ8wJxSZ6rZcuuvw$"
                    "Csxowwf9dQ4yUyB8EtcB8660k2KZ//LWj49us0/9t8o"
                ),
                "is_active": True,
                "failed_login_attempts": 0,
                "locked_until": None,
                "created_at": seeded_at,
                "updated_at": seeded_at,
            }
        ],
    )


def downgrade() -> None:
    """Remove only the dummy user inserted by this migration."""
    op.execute(
        users.delete().where(
            sa.and_(
                users.c.id == DUMMY_USER_ID,
                users.c.email == DUMMY_USER_EMAIL,
            )
        )
    )
