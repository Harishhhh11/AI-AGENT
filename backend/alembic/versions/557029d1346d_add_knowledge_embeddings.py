"""Add knowledge embeddings

Revision ID: 557029d1346d
Revises: c557a58d62e0
Create Date: 2026-08-15 19:55:41.799733
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
import pgvector


revision: str = "557029d1346d"
down_revision: Union[str, Sequence[str], None] = "c557a58d62e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(connection)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    connection = op.get_bind()

    # SQLite DDL is non-transactional, so an interrupted migration can leave
    # additive columns behind while Alembic still reports the old revision.
    if not _column_exists(connection, "knowledge_base", "embedding"):
        op.add_column(
            "knowledge_base",
            sa.Column(
                "embedding",
                pgvector.sqlalchemy.vector.VECTOR(dim=384),
                nullable=True,
            ),
        )

    if not _column_exists(connection, "knowledge_base", "uuid"):
        op.add_column(
            "knowledge_base",
            sa.Column("uuid", sa.UUID(), nullable=True),
        )

    # PostgreSQL has gen_random_uuid(); SQLite does not. Generate UUIDs in
    # Python for SQLite and other dialects while preserving UUID semantics.
    if connection.dialect.name == "postgresql":
        op.execute(
            sa.text(
                "UPDATE knowledge_base "
                "SET uuid = gen_random_uuid() "
                "WHERE uuid IS NULL"
            )
        )
    else:
        rows = connection.execute(
            sa.text("SELECT id FROM knowledge_base WHERE uuid IS NULL")
        ).fetchall()
        for row in rows:
            connection.execute(
                sa.text("UPDATE knowledge_base SET uuid = :uuid WHERE id = :id"),
                {"uuid": str(uuid4()), "id": row[0]},
            )

    op.alter_column("knowledge_base", "uuid", nullable=False)

    if not _column_exists(connection, "knowledge_base", "is_active"):
        op.add_column(
            "knowledge_base",
            sa.Column("is_active", sa.Boolean(), nullable=True),
        )

    op.execute(
        sa.text(
            "UPDATE knowledge_base "
            "SET is_active = TRUE "
            "WHERE is_active IS NULL"
        )
    )
    op.alter_column("knowledge_base", "is_active", nullable=False)

    inspector = sa.inspect(connection)
    index_names = {index["name"] for index in inspector.get_indexes("knowledge_base")}
    expected_index = op.f("ix_knowledge_base_uuid")
    if expected_index not in index_names:
        op.create_index(
            expected_index,
            "knowledge_base",
            ["uuid"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_base_uuid"), table_name="knowledge_base")
    op.drop_column("knowledge_base", "is_active")
    op.drop_column("knowledge_base", "uuid")
    op.drop_column("knowledge_base", "embedding")
