"""
Authentication service.
"""

from sqlalchemy.orm import Session

from app.auth.hashing import verify_password
from app.auth.jwt import create_access_token
from app.repositories.user_repository import UserRepository


class AuthService:

    def __init__(
        self,
        db: Session,
    ):
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