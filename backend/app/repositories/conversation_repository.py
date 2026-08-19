"""
Repository for conversations.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository


class ConversationRepository(
    BaseRepository[Conversation]
):
    """
    Database operations for conversations.
    """

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Conversation,
        )

    def get_by_id(
        self,
        conversation_id: int,
    ) -> Conversation | None:

        statement = (
            select(Conversation)
            .where(
                Conversation.id
                == conversation_id
            )
        )

        return self.db.scalar(
            statement
        )

    def get_by_id_in_organization(
        self,
        conversation_id: int,
        organization_id: int,
    ) -> Conversation | None:

        statement = (
            select(Conversation)
            .where(
                Conversation.id
                == conversation_id
            )
            .where(
                Conversation.organization_id
                == organization_id
            )
        )

        return self.db.scalar(
            statement
        )

    def get_by_session_id(
        self,
        session_id: str,
    ) -> Conversation | None:

        statement = (
            select(Conversation)
            .where(
                Conversation.session_id
                == session_id
            )
        )

        return self.db.scalar(
            statement
        )

    def get_all_in_organization(
        self,
        organization_id: int,
    ) -> list[Conversation]:

        statement = (
            select(Conversation)
            .where(
                Conversation.organization_id
                == organization_id
            )
            .order_by(
                Conversation.id.desc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def get_by_status(
        self,
        organization_id: int,
        status: str,
    ) -> list[Conversation]:

        statement = (
            select(Conversation)
            .where(
                Conversation.organization_id
                == organization_id
            )
            .where(
                Conversation.status
                == status
            )
            .order_by(
                Conversation.id.desc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )