"""
User service.

Contains user business logic while enforcing
organization-level isolation and role assignment.
"""

from sqlalchemy.orm import Session

from app.auth.hashing import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.schemas.user import UserUpdate


class UserService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = UserRepository(db)

    def create_user(
        self,
        user_data: UserCreate,
        organization_id: int,
    ) -> User:

        existing_user = (
            self.repository.get_by_email_in_organization(
                user_data.email,
                organization_id,
            )
        )

        if existing_user:

            raise ValueError(
                "User with this email already exists "
                "in this organization."
            )

        user = User(
            organization_id=organization_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hash_password(
                user_data.password
            ),
        )

        return self.repository.create(user)

    def get_user(
        self,
        user_id: int,
        organization_id: int,
    ) -> User | None:

        return self.repository.get_by_id_in_organization(
            user_id,
            organization_id,
        )

    def get_all_users(
        self,
        organization_id: int,
    ) -> list[User]:

        return self.repository.get_all_in_organization(
            organization_id
        )

    def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        organization_id: int,
    ) -> User | None:

        user = self.repository.get_by_id_in_organization(
            user_id,
            organization_id,
        )

        if user is None:
            return None

        update_data = user_data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():

            setattr(
                user,
                field,
                value,
            )

        return self.repository.update(user)

    def assign_role(
        self,
        user_id: int,
        organization_id: int,
        role_id: int,
    ) -> User | None:
        """Assign an organization-owned role to an organization user."""

        user = self.repository.get_by_id_in_organization(
            user_id,
            organization_id,
        )

        if user is None:
            return None

        role = self.repository.get_role_in_organization(
            role_id,
            organization_id,
        )

        if role is None:
            raise ValueError("Role not found in this organization.")

        if role not in user.roles:
            user.roles.append(role)

        return self.repository.update(user)

    def remove_role(
        self,
        user_id: int,
        organization_id: int,
        role_id: int,
    ) -> User | None:
        """Remove an organization-owned role from an organization user."""

        user = self.repository.get_by_id_in_organization(
            user_id,
            organization_id,
        )

        if user is None:
            return None

        role = self.repository.get_role_in_organization(
            role_id,
            organization_id,
        )

        if role is None:
            raise ValueError("Role not found in this organization.")

        if role in user.roles:
            user.roles.remove(role)

        return self.repository.update(user)

    def delete_user(
        self,
        user_id: int,
        organization_id: int,
    ) -> bool:

        user = self.repository.get_by_id_in_organization(
            user_id,
            organization_id,
        )

        if user is None:
            return False

        self.repository.delete(user)

        return True
