"""
User repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: Session):
        super().__init__(
            db=db,
            model=User,
        )

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        statement = select(User).where(
            User.email == email
        )

        return self.db.scalar(statement)

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        statement = select(User).where(
            User.id == user_id
        )

        return self.db.scalar(statement)

    def get_by_organization(
        self,
        organization_id: int,
    ) -> list[User]:

        statement = (
            select(User)
            .where(
                User.organization_id
                == organization_id
            )
            .order_by(User.id.desc())
        )

        return list(
            self.db.scalars(statement).all()
        )