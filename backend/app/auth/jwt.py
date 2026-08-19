"""
JWT utilities.
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt

from app.core.config import settings


ALGORITHM = "HS256"


def create_access_token(
    data: dict,
    expires_minutes: int = 30,
) -> str:

    payload = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=expires_minutes
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
):

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
    )
def create_token_pair(
    user,
):

    access_token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
        }
    )

    return access_token