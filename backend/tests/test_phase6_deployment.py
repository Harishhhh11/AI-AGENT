from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_is_non_root_and_has_healthcheck():
    dockerfile = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")

    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "docker-entrypoint.sh" in dockerfile
    assert "--proxy-headers" in dockerfile


def test_entrypoint_runs_migrations_by_default():
    entrypoint = (ROOT / "backend" / "docker-entrypoint.sh").read_text(encoding="utf-8")

    assert 'RUN_MIGRATIONS:-true' in entrypoint
    assert "alembic upgrade head" in entrypoint
    assert 'exec "$@"' in entrypoint


def test_compose_has_no_source_mount_and_has_healthcheck():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    backend = compose["services"]["backend"]

    assert backend["restart"] == "unless-stopped"
    assert backend["environment"]["RUN_MIGRATIONS"] == "true"
    assert "volumes" not in backend
    assert backend["healthcheck"]["retries"] == 3
    assert "ai-receptionist" in compose["networks"]
