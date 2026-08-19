"""Add knowledge embeddings

Revision ID: 557029d1346d
Revises: c557a58d62e0
Create Date: 2026-08-15 19:55:41.799733

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = "557029d1346d"
down_revision: Union[str, Sequence[str], None] = "c557a58d62e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---------------------------------------------------------
    # 1. Add embedding column
    # ---------------------------------------------------------

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

    op.add_column(
        "knowledge_base",
        sa.Column(
            "uuid",
            sa.UUID(),
            nullable=True,
        ),
    )

    # Generate UUID values for existing rows.
    op.execute(
        """
        UPDATE knowledge_base
        SET uuid = gen_random_uuid()
        WHERE uuid IS NULL
        """
    )

    # UUID is now populated for existing rows.
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

    op.alter_column(
        "knowledge_base",
        "is_active",
        nullable=False,
    )

    # ---------------------------------------------------------
    # 4. UUID index
    # ---------------------------------------------------------

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