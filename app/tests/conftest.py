"""Shared integration test fixtures."""

import base64
import os

os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-that-is-at-least-32-characters"
os.environ["ENCRYPTION_KEY"] = base64.urlsafe_b64encode(b"k" * 32).decode()
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import limiter
from app.database.base import Base
from app.database.session import get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)


def override_db():
    """Yield the isolated test session."""
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
limiter.enabled = False


@pytest.fixture(autouse=True)
def clean_database():
    """Recreate the schema around each test."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> TestClient:
    """Return a test API client."""
    return TestClient(app)


@pytest.fixture
def db() -> Session:
    """Return a direct database session."""
    with TestingSession() as session:
        yield session


@pytest.fixture
def user_payload() -> dict[str, str]:
    return {
        "fullname": "Vault Owner",
        "email": "owner@example.com",
        "password": "VeryStrong1!Password",
    }


@pytest.fixture
def authenticated(client: TestClient, user_payload: dict[str, str]) -> dict:
    client.post("/api/v1/auth/register", json=user_payload)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    tokens = response.json()["data"]
    return {
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
        "tokens": tokens,
    }
