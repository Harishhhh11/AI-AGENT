"""Add publishable AI receptionists.

Revision ID: d2c4b7a8e901
Revises: 557029d1346d
Create Date: 2026-08-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2c4b7a8e901"
down_revision: Union[str, Sequence[str], None] = "557029d1346d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("public_slug", sa.String(length=100), nullable=False),
        sa.Column("welcome_message", sa.Text(), nullable=False),
        sa.Column("system_instructions", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_slug"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_agents_id"), "agents", ["id"], unique=False)
    op.create_index(op.f("ix_agents_organization_id"), "agents", ["organization_id"], unique=False)
    op.create_index(op.f("ix_agents_public_slug"), "agents", ["public_slug"], unique=True)
    op.create_index(op.f("ix_agents_uuid"), "agents", ["uuid"], unique=True)

    # Nullable columns preserve all existing organization-level data. New
    # public conversations receive agent_id through ConversationService.
    op.add_column("conversations", sa.Column("agent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_conversations_agent_id_agents",
        "conversations",
        "agents",
        ["agent_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_conversations_agent_id"), "conversations", ["agent_id"], unique=False)

    # NULL knowledge remains shared by every receptionist in the company.
    op.add_column("knowledge_base", sa.Column("agent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_knowledge_base_agent_id_agents",
        "knowledge_base",
        "agents",
        ["agent_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_knowledge_base_agent_id"), "knowledge_base", ["agent_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_base_agent_id"), table_name="knowledge_base")
    op.drop_constraint("fk_knowledge_base_agent_id_agents", "knowledge_base", type_="foreignkey")
    op.drop_column("knowledge_base", "agent_id")
    op.drop_index(op.f("ix_conversations_agent_id"), table_name="conversations")
    op.drop_constraint("fk_conversations_agent_id_agents", "conversations", type_="foreignkey")
    op.drop_column("conversations", "agent_id")
    op.drop_index(op.f("ix_agents_uuid"), table_name="agents")
    op.drop_index(op.f("ix_agents_public_slug"), table_name="agents")
    op.drop_index(op.f("ix_agents_organization_id"), table_name="agents")
    op.drop_index(op.f("ix_agents_id"), table_name="agents")
    op.drop_table("agents")
