"""Add knowledge embeddings

Revision ID: 557029d1346d
Revises: c557a58d62e0
Create Date: 2026-08-15 19:55:41.799733

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "557029d1346d"
down_revision: Union[str, Sequence[str], None] = "c557a58d62e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    existing_columns = {
        column["name"] for column in inspect(bind).get_columns("knowledge_base")
    }

    # ---------------------------------------------------------
    # 1. Add embedding column
    # ---------------------------------------------------------

    if "embedding" not in existing_columns:
        op.add_column(
            "knowledge_base",
            sa.Column(
                "embedding",
                pgvector.sqlalchemy.vector.VECTOR(dim=384),
                nullable=True,
            ),
        )

    # ---------------------------------------------------------
    # 2. Add UUID column safely
    #
    # Existing knowledge_base rows already exist, therefore
    # UUID cannot initially be NOT NULL.
    # ---------------------------------------------------------

    if "uuid" not in existing_columns:
        op.add_column(
            "knowledge_base",
            sa.Column(
                "uuid",
                sa.UUID(),
                nullable=True,
            ),
        )

    # Generate UUID values for existing rows. SQLite does not provide
    # PostgreSQL's gen_random_uuid(), so use its random blob function locally.
    dialect_name = bind.dialect.name
    if dialect_name == "sqlite":
        op.execute(
            """
            UPDATE knowledge_base
            SET uuid = lower(hex(randomblob(16)))
            WHERE uuid IS NULL
            """
        )
    elif dialect_name == "postgresql":
        op.execute(
            """
            UPDATE knowledge_base
            SET uuid = gen_random_uuid()
            WHERE uuid IS NULL
            """
        )
    else:
        raise RuntimeError(
            f"Unsupported database dialect for UUID backfill: {dialect_name}"
        )

    # UUID is now populated for existing rows.
    if dialect_name != "sqlite":
        op.alter_column(
            "knowledge_base",
            "uuid",
            nullable=False,
        )

    # ---------------------------------------------------------
    # 3. Add is_active safely
    #
    # Existing rows need a value before NOT NULL is applied.
    # ---------------------------------------------------------

    if "is_active" not in existing_columns:
        op.add_column(
            "knowledge_base",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=True,
            ),
        )

    # Existing knowledge records should be active.
    op.execute(
        """
        UPDATE knowledge_base
        SET is_active = TRUE
        WHERE is_active IS NULL
        """
    )

    if dialect_name != "sqlite":
        op.alter_column(
            "knowledge_base",
            "is_active",
            nullable=False,
        )

    # ---------------------------------------------------------
    # 4. UUID index
    # ---------------------------------------------------------

    existing_indexes = {
        index["name"] for index in inspect(bind).get_indexes("knowledge_base")
    }
    if "ix_knowledge_base_uuid" not in existing_indexes:
        op.create_index(
            op.f("ix_knowledge_base_uuid"),
            "knowledge_base",
            ["uuid"],
            unique=True,
        )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove UUID index.
    op.drop_index(
        op.f("ix_knowledge_base_uuid"),
        table_name="knowledge_base",
    )

    # Remove columns added by this migration.
    op.drop_column(
        "knowledge_base",
        "is_active",
    )

    op.drop_column(
        "knowledge_base",
        "uuid",
    )

    op.drop_column(
        "knowledge_base",
        "embedding",
    )