"""Password hashing and policy."""

import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
DUMMY_PASSWORD_HASH = hasher.hash("Dummy1!Password")


def hash_password(password: str) -> str:
    """Hash a user password with Argon2id."""
    return hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password without leaking hash errors."""
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def validate_password_strength(value: str) -> str:
    """Enforce the password complexity policy."""
    if (
        len(value) < 12
        or not re.search(r"[A-Z]", value)
        or not re.search(r"[a-z]", value)
        or not re.search(r"\d", value)
        or not re.search(r"[^A-Za-z0-9]", value)
    ):
        raise ValueError(
            "Password must be at least 12 characters and include uppercase, "
            "lowercase, number, and special character"
        )
    return value
