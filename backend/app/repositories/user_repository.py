"""User repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
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

    def get_by_id_in_organization(
        self,
        user_id: int,
        organization_id: int,
    ) -> User | None:

        statement = (
            select(User)
            .where(User.id == user_id)
            .where(User.organization_id == organization_id)
        )

        return self.db.scalar(statement)

    def get_by_email_in_organization(
        self,
        email: str,
        organization_id: int,
    ) -> User | None:

        statement = (
            select(User)
            .where(User.email == email)
            .where(User.organization_id == organization_id)
        )

        return self.db.scalar(statement)

    def get_role_in_organization(
        self,
        role_id: int,
        organization_id: int,
    ) -> Role | None:

        statement = (
            select(Role)
            .where(Role.id == role_id)
            .where(Role.organization_id == organization_id)
        )

        return self.db.scalar(statement)

    def add_role(
        self,
        user: User,
        role: Role,
    ) -> User:
        if role not in user.roles:
            user.roles.append(role)
        self.db.flush()
        return user

    def remove_role(
        self,
        user: User,
        role: Role,
    ) -> User:
        if role in user.roles:
            user.roles.remove(role)
        self.db.flush()
        return user
