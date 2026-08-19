from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_conversation(
        self,
        conversation_id: int,
    ) -> list[Message]:

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

        return list(
            self.db.scalars(statement).all()
        )