"""
Authentication dependencies.

Provides JWT Bearer authentication for protected APIs.
"""

from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database.session import get_db
from app.models.user import User


security = HTTPBearer(
    auto_error=True,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(
        get_db
    ),
) -> User:
    """
    Extract the JWT token, validate it,
    and return the authenticated User.
    """

    token = credentials.credentials

    try:

        payload = decode_access_token(
            token
        )

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user_id = payload.get(
        "user_id"
    )

    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return user