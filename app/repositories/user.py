"""User persistence repository."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Encapsulate user database access."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(self, fullname: str, email: str, password_hash: str) -> User:
        user = User(fullname=fullname, email=email.lower(), password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def record_failed_login(
        self, user: User, attempts: int, locked_until: datetime | None
    ) -> None:
        user.failed_login_attempts = attempts
        user.locked_until = locked_until
        self.db.commit()

    def reset_failed_logins(self, user: User) -> None:
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()
