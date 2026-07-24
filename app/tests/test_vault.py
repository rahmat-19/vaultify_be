"""Vault CRUD, encryption, search, and isolation tests."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vault_item import VaultItem


def test_vault_crud_and_encryption(
    client: TestClient, authenticated: dict, db: Session
) -> None:
    payload = {
        "title": "GitHub",
        "username": "owner@example.com",
        "password": "repository-secret",
        "notes": "recovery codes",
        "website": "https://github.com",
        "category": "login",
    }
    created = client.post(
        "/api/v1/vault", headers=authenticated["headers"], json=payload
    )
    assert created.status_code == 201
    item = created.json()["data"]
    assert item["password"] == payload["password"]

    stored = db.scalar(select(VaultItem).where(VaultItem.id == uuid.UUID(item["id"])))
    assert stored is not None
    assert payload["password"] not in stored.encrypted_password
    assert payload["notes"] not in stored.encrypted_notes

    listed = client.get("/api/v1/vault", headers=authenticated["headers"])
    assert len(listed.json()["data"]) == 1

    updated = client.put(
        f"/api/v1/vault/{item['id']}",
        headers=authenticated["headers"],
        json={"title": "GitHub Updated", "password": "new-secret"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["password"] == "new-secret"

    searched = client.get(
        "/api/v1/vault/search?q=updated", headers=authenticated["headers"]
    )
    assert len(searched.json()["data"]) == 1

    deleted = client.delete(
        f"/api/v1/vault/{item['id']}", headers=authenticated["headers"]
    )
    assert deleted.status_code == 200
    assert (
        client.get(
            f"/api/v1/vault/{item['id']}", headers=authenticated["headers"]
        ).status_code
        == 404
    )


def test_cross_user_access_is_hidden(client: TestClient, authenticated: dict) -> None:
    item = client.post(
        "/api/v1/vault",
        headers=authenticated["headers"],
        json={"title": "Private", "password": "secret"},
    ).json()["data"]
    second = {
        "fullname": "Second User",
        "email": "second@example.com",
        "password": "AnotherStrong1!Password",
    }
    client.post("/api/v1/auth/register", json=second)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": second["email"], "password": second["password"]},
    ).json()["data"]
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    assert client.get(f"/api/v1/vault/{item['id']}", headers=headers).status_code == 404
    assert (
        client.delete(f"/api/v1/vault/{item['id']}", headers=headers).status_code == 404
    )
