"""Authentication integration tests."""

from fastapi.testclient import TestClient


def test_register(client: TestClient, user_payload: dict[str, str]) -> None:
    response = client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == user_payload["email"]
    assert "password" not in body["data"]


def test_duplicate_email_rejected(
    client: TestClient, user_payload: dict[str, str]
) -> None:
    client.post("/api/v1/auth/register", json=user_payload)
    response = client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 409
    assert response.json()["success"] is False


def test_login_and_me(client: TestClient, user_payload: dict[str, str]) -> None:
    client.post("/api/v1/auth/register", json=user_payload)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login.status_code == 200
    tokens = login.json()["data"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == user_payload["email"]


def test_refresh_rotates_token(client: TestClient, authenticated: dict) -> None:
    old_token = authenticated["tokens"]["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": old_token})
    assert response.status_code == 200
    assert response.json()["data"]["refresh_token"] != old_token
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": old_token})
    assert reused.status_code == 401


def test_logout_revokes_refresh(client: TestClient, authenticated: dict) -> None:
    refresh_token = authenticated["tokens"]["refresh_token"]
    response = client.post(
        "/api/v1/auth/logout",
        headers=authenticated["headers"],
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        ).status_code
        == 401
    )


def test_unauthorized_access(client: TestClient) -> None:
    response = client.get("/api/v1/vault")
    assert response.status_code == 401
    assert response.json()["success"] is False
