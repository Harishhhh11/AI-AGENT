"""
Refresh token repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import (
    BaseRepository,
)


class RefreshTokenRepository(
    BaseRepository[RefreshToken]
):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            RefreshToken,
            db,
        )

    def get_by_token(
        self,
        token: str,
    ) -> RefreshToken | None:

        stmt = select(
            RefreshToken
        ).where(
            RefreshToken.token == token
        )

        return self.db.scalar(stmt)