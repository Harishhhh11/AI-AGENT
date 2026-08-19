"""
Refresh token service.
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)


class TokenService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = RefreshTokenRepository(db)

    def create_refresh_token(
        self,
        user_id: int,
    ) -> RefreshToken:

        token = str(uuid4())

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(
                timezone.utc
            ) + timedelta(days=30),
        )

        return self.repository.create(
            refresh_token
        )

    def validate_refresh_token(
        self,
        token: str,
    ):

        refresh_token = self.repository.get_by_token(
            token
        )

        if refresh_token is None:
            return None

        if refresh_token.expires_at < datetime.now(
            timezone.utc
        ):
            return None

        return refresh_token

    def revoke_refresh_token(
        self,
        token: str,
    ):

        refresh_token = self.repository.get_by_token(
            token
        )

        if refresh_token:
            self.repository.delete(
                refresh_token
            )