"""
Conversation service.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repository import (
    ConversationRepository,
)


ALLOWED_STATUSES = {
    "active",
    "closed",
}


class ConversationService:
    """
    Service responsible for conversations and messages.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

        self.repository = ConversationRepository(db)

    # =========================================================
    # GET OR CREATE CONVERSATION
    # =========================================================

    def get_or_create_conversation(
        self,
        session_id: str | None,
        organization_id: int,
        user_id: int | None = None,
        agent_id: int | None = None,
    ) -> Conversation:

        conversation = None

        # -----------------------------------------------------
        # Try existing conversation
        # -----------------------------------------------------

        if session_id:

            conversation = (
                self.repository
                .get_by_session_id(
                    session_id
                )
            )

            # Prevent cross-organization access.
            if (
                conversation
                and conversation.organization_id
                != organization_id
            ):
                conversation = None

            # A session created for one receptionist must never be reused
            # by another receptionist, even inside the same organization.
            if conversation and conversation.agent_id != agent_id:
                conversation = None
                # session_id is globally unique. Do not reuse an ID owned by
                # a different receptionist when starting a new conversation.
                session_id = None

        # -----------------------------------------------------
        # Existing conversation
        # -----------------------------------------------------

        if conversation:

            return conversation

        # -----------------------------------------------------
        # Create new conversation
        # -----------------------------------------------------

        # session_id is NOT NULL in the database,
        # therefore generate one when the frontend
        # does not provide it.
        if not session_id:

            import uuid

            session_id = str(
                uuid.uuid4()
            )

        conversation = Conversation(
            organization_id=organization_id,
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            status="active",
        )

        self.repository.add(
            conversation
        )

        self.db.commit()

        self.db.refresh(
            conversation
        )

        return conversation

    # =========================================================
    # ADD MESSAGE
    # =========================================================

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)

        self.db.commit()

        self.db.refresh(message)

        return message

    # =========================================================
    # GET MESSAGES
    # =========================================================

    def get_messages(
        self,
        conversation_id: int,
    ) -> list[Message]:
        """
        Return actual Message ORM objects.

        IMPORTANT:
        Do not use Message.__table__.select()
        here because that returns Row objects and
        row[0] would be the message ID.

        We need ORM Message objects because callers
        access:
            message.id
            message.role
            message.content
            message.created_at
        """

        statement = (
            select(Message)
            .where(
                Message.conversation_id
                == conversation_id
            )
            .order_by(
                Message.id.asc()
            )
        )

        result = self.db.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    # =========================================================
    # GET CONVERSATION
    # =========================================================

    def get_conversation(
        self,
        conversation_id: int,
        organization_id: int,
    ) -> Conversation | None:

        return (
            self.repository
            .get_by_id_in_organization(
                conversation_id,
                organization_id,
            )
        )

    # =========================================================
    # GET ALL CONVERSATIONS
    # =========================================================

    def get_all_conversations(
        self,
        organization_id: int,
    ) -> list[Conversation]:

        return (
            self.repository
            .get_all_in_organization(
                organization_id
            )
        )

    # =========================================================
    # GET CONVERSATIONS BY STATUS
    # =========================================================

    def get_conversations_by_status(
        self,
        organization_id: int,
        status: str,
    ) -> list[Conversation]:

        return (
            self.repository
            .get_by_status(
                organization_id,
                status,
            )
        )

    # =========================================================
    # UPDATE STATUS
    # =========================================================

    def update_status(
        self,
        conversation_id: int,
        organization_id: int,
        status: str,
    ) -> Conversation | None:

        if status not in ALLOWED_STATUSES:

            raise ValueError(
                f"Invalid conversation status: "
                f"{status}"
            )

        conversation = (
            self.repository
            .get_by_id_in_organization(
                conversation_id,
                organization_id,
            )
        )

        if conversation is None:

            return None

        conversation.status = status

        self.db.commit()

        self.db.refresh(
            conversation
        )

        return conversation
