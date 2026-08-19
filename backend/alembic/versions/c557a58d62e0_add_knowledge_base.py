"""Add knowledge base

Revision ID: REPLACE_WITH_GENERATED_ID
Revises: ba123f69320f
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c557a58d62e0'

down_revision: Union[
    str,
    Sequence[str],
    None
] = "ba123f69320f"

branch_labels: Union[
    str,
    Sequence[str],
    None
] = None

depends_on: Union[
    str,
    Sequence[str],
    None
] = None


def upgrade() -> None:

    op.create_table(
        "knowledge_base",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "organization_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "source",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        op.f("ix_knowledge_base_id"),
        "knowledge_base",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_knowledge_base_organization_id"),
        "knowledge_base",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        op.f(
            "ix_knowledge_base_organization_id"
        ),
        table_name="knowledge_base",
    )

    op.drop_index(
        op.f("ix_knowledge_base_id"),
        table_name="knowledge_base",
    )

    op.drop_table(
        "knowledge_base"
    )