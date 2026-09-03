"""
Authentication service.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.bootstrap import ADMIN_ROLE_NAME, ensure_organization_admin_role
from app.auth.hashing import verify_password
from app.auth.jwt import create_access_token
from app.models.role import Role
from app.repositories.user_repository import UserRepository


class AuthService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = UserRepository(db)

    def login(
        self,
        email: str,
        password: str,
    ):

        user = self.repository.get_by_email(
            email
        )

        if user is None:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        # Repair the canonical organization-admin role permissions for
        # existing tenants created before newer permissions were added.
        # This only runs when the user already has organization_admin, so
        # ordinary users are never elevated during login.
        admin_role = self.db.scalar(
            select(Role)
            .where(Role.organization_id == user.organization_id)
            .where(Role.name == ADMIN_ROLE_NAME)
        )

        if admin_role is not None and admin_role in user.roles:
            ensure_organization_admin_role(
                self.db,
                user.organization_id,
            )
            self.db.commit()

        token = create_access_token(
            {
                "user_id": user.id,
                "email": user.email,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }
