from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_success(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_password_hash", hash_password("testpass123"))

    response = client.post(
        "/api/auth/login",
        data={"username": settings.admin_username, "password": "testpass123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body


def test_login_wrong_password(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_password_hash", hash_password("testpass123"))

    response = client.post(
        "/api/auth/login",
        data={"username": settings.admin_username, "password": "wrong"},
    )
    assert response.status_code == 401
