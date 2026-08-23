from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config.settings import Settings
from app.main import app


def test_health_is_liveness_only():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Request-ID" in response.headers


def test_request_id_is_preserved():
    client = TestClient(app)
    request_id = "phase6-test-request-id"

    response = client.get("/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_ready_reports_database_state():
    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    body = response.json()
    assert body["status"] in {"ready", "not_ready"}
    assert body["dependencies"]["database"] in {"available", "unavailable"}


def test_production_rejects_debug_mode():
    try:
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="x" * 64,
            DATABASE_URL="sqlite:///./ci_test.db",
        )
    except ValidationError:
        return
    raise AssertionError("production settings must reject DEBUG=True")


def test_production_rejects_placeholder_secret():
    try:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY",
            DATABASE_URL="sqlite:///./ci_test.db",
        )
    except ValidationError:
        return
    raise AssertionError("production settings must reject the placeholder secret")


def test_production_accepts_strong_secret_and_explicit_origins():
    settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="s" * 64,
        DATABASE_URL="sqlite:///./ci_test.db",
        CORS_ALLOWED_ORIGINS="https://example.com",
    )

    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False
    assert settings.cors_allowed_origins == ["https://example.com"]
