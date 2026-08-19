"""
Repository for lead records.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead

from app.repositories.base_repository import (
    BaseRepository,
)


class LeadRepository(
    BaseRepository[Lead]
):
    """
    Database operations for leads.

    All organization-specific operations explicitly filter
    by organization_id where appropriate.
    """

    def __init__(
        self,
        db: Session,
    ):

        super().__init__(
            db=db,
            model=Lead,
        )

    # =========================================================
    # GET BY ID
    # =========================================================

    def get_by_id(
        self,
        lead_id: int,
    ) -> Lead | None:

        statement = (
            select(Lead)
            .where(
                Lead.id
                == lead_id
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # GET BY ID + ORGANIZATION
    # =========================================================

    def get_by_id_in_organization(
        self,
        lead_id: int,
        organization_id: int,
    ) -> Lead | None:

        statement = (
            select(Lead)
            .where(
                Lead.id
                == lead_id
            )
            .where(
                Lead.organization_id
                == organization_id
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # GET BY CONVERSATION
    # =========================================================

    def get_by_conversation(
        self,
        conversation_id: int,
    ) -> Lead | None:

        statement = (
            select(Lead)
            .where(
                Lead.conversation_id
                == conversation_id
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # GET BY CONVERSATION + ORGANIZATION
    # =========================================================

    def get_by_conversation_in_organization(
        self,
        conversation_id: int,
        organization_id: int,
    ) -> Lead | None:

        statement = (
            select(Lead)
            .where(
                Lead.conversation_id
                == conversation_id
            )
            .where(
                Lead.organization_id
                == organization_id
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # GET BY PHONE
    # =========================================================

    def get_by_phone_in_organization(
        self,
        phone: str,
        organization_id: int,
    ) -> Lead | None:

        if not phone:

            return None

        statement = (
            select(Lead)
            .where(
                Lead.organization_id
                == organization_id
            )
            .where(
                Lead.phone
                == phone
            )
            .order_by(
                Lead.id.desc()
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # GET BY EMAIL
    # =========================================================

    def get_by_email_in_organization(
        self,
        email: str,
        organization_id: int,
    ) -> Lead | None:

        if not email:

            return None

        statement = (
            select(Lead)
            .where(
                Lead.organization_id
                == organization_id
            )
            .where(
                Lead.email
                == email
            )
            .order_by(
                Lead.id.desc()
            )
        )

        return self.db.scalar(
            statement
        )

    # =========================================================
    # GET ALL
    # =========================================================

    def get_all_in_organization(
        self,
        organization_id: int,
    ) -> list[Lead]:

        statement = (
            select(Lead)
            .where(
                Lead.organization_id
                == organization_id
            )
            .order_by(
                Lead.id.desc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    # =========================================================
    # GET BY STATUS
    # =========================================================

    def get_by_status(
        self,
        organization_id: int,
        status: str,
    ) -> list[Lead]:

        statement = (
            select(Lead)
            .where(
                Lead.organization_id
                == organization_id
            )
            .where(
                Lead.status
                == status
            )
            .order_by(
                Lead.id.desc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )