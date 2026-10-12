from fastapi.testclient import TestClient

from services.api.auth import authenticate
from services.api.main import app


def test_authentication_is_disabled_for_local_development(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    assert authenticate() is None


def test_health_endpoint_is_public():
    response = TestClient(app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_production_auth_requires_a_token(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    response = TestClient(app).get("/api/tasks")
    assert response.status_code == 401
