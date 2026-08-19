"""Add conversations and messages

Revision ID: 60613161696f
Revises: e1ab76504b9f
Create Date: 2026-08-15
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "60613161696f"
down_revision: Union[str, Sequence[str], None] = "e1ab76504b9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "conversations",

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
            "user_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "session_id",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=30),
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
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        op.f("ix_conversations_id"),
        "conversations",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_conversations_organization_id"),
        "conversations",
        ["organization_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_conversations_user_id"),
        "conversations",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_conversations_session_id"),
        "conversations",
        ["session_id"],
        unique=True,
    )

    op.create_table(
        "messages",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "conversation_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "role",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        op.f("ix_messages_id"),
        "messages",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_messages_conversation_id"),
        "messages",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_messages_conversation_id"),
        table_name="messages",
    )

    op.drop_index(
        op.f("ix_messages_id"),
        table_name="messages",
    )

    op.drop_table(
        "messages"
    )

    op.drop_index(
        op.f("ix_conversations_session_id"),
        table_name="conversations",
    )

    op.drop_index(
        op.f("ix_conversations_user_id"),
        table_name="conversations",
    )

    op.drop_index(
        op.f("ix_conversations_organization_id"),
        table_name="conversations",
    )

    op.drop_index(
        op.f("ix_conversations_id"),
        table_name="conversations",
    )

    op.drop_table(
        "conversations"
    )