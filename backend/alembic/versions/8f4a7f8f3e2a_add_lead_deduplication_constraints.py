"""Add organization-scoped lead deduplication constraints.

Revision ID: 8f4a7f8f3e2a
Revises: d2c4b7a8e901
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8f4a7f8f3e2a"
down_revision: Union[str, Sequence[str], None] = "d2c4b7a8e901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL permits multiple NULL values in these unique constraints,
    # while preventing duplicate known identity keys per organization.
    op.create_index(
        "uq_leads_organization_conversation",
        "leads",
        ["organization_id", "conversation_id"],
        unique=True,
    )
    op.create_index(
        "uq_leads_organization_phone",
        "leads",
        ["organization_id", "phone"],
        unique=True,
    )
    op.create_index(
        "uq_leads_organization_email",
        "leads",
        ["organization_id", "email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_leads_organization_email", table_name="leads")
    op.drop_index("uq_leads_organization_phone", table_name="leads")
    op.drop_index("uq_leads_organization_conversation", table_name="leads")
