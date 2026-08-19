"""Add leads

Revision ID: ba123f69320f
Revises: 60613161696f
Create Date: 2026-08-15
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ba123f69320f"

down_revision: Union[
    str,
    Sequence[str],
    None
] = "60613161696f"

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
        "leads",

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
            "conversation_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "name",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "phone",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "email",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "interest",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "preferred_mode",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "preferred_time",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
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

        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        op.f("ix_leads_id"),
        "leads",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_leads_organization_id"),
        "leads",
        ["organization_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_leads_conversation_id"),
        "leads",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_leads_conversation_id"),
        table_name="leads",
    )

    op.drop_index(
        op.f("ix_leads_organization_id"),
        table_name="leads",
    )

    op.drop_index(
        op.f("ix_leads_id"),
        table_name="leads",
    )

    op.drop_table(
        "leads"
    )