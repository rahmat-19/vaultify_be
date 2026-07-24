"""Cryptography and validation unit tests."""

import base64

import pytest
from cryptography.exceptions import InvalidTag
from fastapi.testclient import TestClient

from app.security.encryption import EncryptionService


def test_encryption_round_trip_and_random_nonce() -> None:
    service = EncryptionService(base64.urlsafe_b64encode(b"x" * 32).decode())
    first = service.encrypt("sensitive")
    second = service.encrypt("sensitive")
    assert first != second
    assert service.decrypt(first) == "sensitive"


def test_tampered_ciphertext_rejected() -> None:
    service = EncryptionService(base64.urlsafe_b64encode(b"x" * 32).decode())
    encrypted = service.encrypt("sensitive")
    assert encrypted is not None
    with pytest.raises((InvalidTag, ValueError)):
        service.decrypt(encrypted[:-2] + "AA")


@pytest.mark.parametrize(
    "password",
    ["short", "alllowercase123!", "NOLOWERCASE123!", "NoNumberHere!", "NoSpecial123"],
)
def test_weak_password_validation(client: TestClient, password: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "Test User",
            "email": "test@example.com",
            "password": password,
        },
    )
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_invalid_vault_url(client: TestClient, authenticated: dict) -> None:
    response = client.post(
        "/api/v1/vault",
        headers=authenticated["headers"],
        json={"title": "Bad URL", "website": "javascript:alert(1)"},
    )
    assert response.status_code == 422


def test_swagger_assets_allowed_by_csp(client: TestClient) -> None:
    """Swagger's CDN assets must not be blocked by security middleware."""
    response = client.get("/docs")
    assert response.status_code == 200
    policy = response.headers["content-security-policy"]
    assert "https://cdn.jsdelivr.net" in policy
    assert "connect-src 'self'" in policy
