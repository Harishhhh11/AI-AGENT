"""JWT utilities used by the authentication layer."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


ALGORITHM = "HS256"


def create_access_token(
    data: dict[str, Any],
    expires_minutes: int = 30,
) -> str:
    """Create a signed JWT access token."""

    payload = dict(data)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises ``JWTError`` when the token is invalid or expired.
    """

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    return dict(payload)


def create_token_pair(user) -> str:
    """Create the current access token for a user.

    The function name is retained for API compatibility; the platform
    currently issues one access token rather than a refresh-token pair.
    """

    return create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
        }
    )


__all__ = [
    "ALGORITHM",
    "JWTError",
    "create_access_token",
    "decode_access_token",
    "create_token_pair",
]
