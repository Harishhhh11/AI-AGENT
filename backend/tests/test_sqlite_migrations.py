"""Regression coverage for SQLite Alembic upgrades."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


BACKEND_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE_REVISION = "c557a58d62e0"
HEAD_REVISION = "8f4a7f8f3e2a"


def _alembic_environment(database_url: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        DATABASE_URL=database_url,
        DEBUG="false",
    )
    return environment


def _run_alembic(
    database_url: str,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=_alembic_environment(database_url),
        text=True,
        capture_output=True,
        check=True,
    )


def test_fresh_sqlite_upgrade_preserves_knowledge_embeddings_data(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}"

    _run_alembic(database_url, "upgrade", KNOWLEDGE_BASE_REVISION)

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO organizations
                    (id, name, email, uuid, is_active, created_at, updated_at)
                VALUES
                    (1, 'Acme', 'owner@acme.example', '11111111-1111-1111-1111-111111111111',
                     1, '2026-01-01 00:00:00', '2026-01-01 00:00:00')
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO knowledge_base
                    (id, organization_id, title, content, source, category, created_at, updated_at)
                VALUES
                    (1, 1, 'Hours', 'Open weekdays', 'manual', 'faq',
                     '2026-01-01 00:00:00', '2026-01-01 00:00:00')
                """
            )
        )

    _run_alembic(database_url, "upgrade", "head")
    current = _run_alembic(database_url, "current")

    inspector = inspect(engine)
    columns = {
        column["name"]: column
        for column in inspector.get_columns("knowledge_base")
    }
    indexes = inspector.get_indexes("knowledge_base")

    assert current.stdout.strip() == f"{HEAD_REVISION} (head)"
    assert not columns["uuid"]["nullable"]
    assert not columns["is_active"]["nullable"]
    assert "embedding" in columns
    assert any(
        index["name"] == "ix_knowledge_base_uuid" and index["unique"]
        for index in indexes
    )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT title, content, source, category, uuid, is_active, embedding
                FROM knowledge_base
                WHERE id = 1
                """
            )
        ).mappings().one()
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    assert row["title"] == "Hours"
    assert row["content"] == "Open weekdays"
    assert row["source"] == "manual"
    assert row["category"] == "faq"
    assert row["uuid"]
    assert bool(row["is_active"]) is True
    assert row["embedding"] is None
    assert revision == HEAD_REVISION


def test_knowledge_embedding_migration_keeps_native_postgresql_alters() -> None:
    migration = (
        BACKEND_DIR
        / "alembic"
        / "versions"
        / "557029d1346d_add_knowledge_embeddings.py"
    ).read_text(encoding="utf-8")

    assert 'connection.dialect.name == "sqlite"' in migration
    assert 'op.batch_alter_table(' in migration
    assert 'op.alter_column("knowledge_base", "uuid", nullable=False)' in migration
    assert 'op.alter_column("knowledge_base", "is_active", nullable=False)' in migration
