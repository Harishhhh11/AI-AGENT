from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import Settings


ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_production_compose_has_private_postgres_and_tls_proxy():
    compose = yaml.safe_load(
        (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
    )

    assert compose["services"]["db"]["image"] == "pgvector/pgvector:pg16"
    assert compose["services"]["db"]["healthcheck"]["retries"] == 5
    assert compose["services"]["caddy"]["ports"] == ["80:80", "443:443"]
    assert compose["networks"]["private"]["internal"] is True


def test_production_settings_reject_unsafe_values():
    with pytest.raises(ValueError, match="DEBUG"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="x" * 40,
            DATABASE_URL="postgresql+psycopg://user:pass@db/app",
            CORS_ALLOWED_ORIGINS="https://app.example.com",
        )

    with pytest.raises(ValueError, match="SQLite"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="x" * 40,
            DATABASE_URL="sqlite:///./app.db",
            CORS_ALLOWED_ORIGINS="https://app.example.com",
        )


def test_metrics_endpoint_is_private_schema_and_backup_script_exists():
    main = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    backup = ROOT / "scripts" / "backup-postgres.sh"

    assert '@app.get("/metrics", include_in_schema=False)' in main
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "app_uptime_seconds" in response.text
    assert backup.exists()
    assert "pg_dump" in backup.read_text(encoding="utf-8")
