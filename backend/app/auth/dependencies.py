"""
Authentication dependencies.

Provides JWT Bearer authentication for protected APIs and enforces
that the authenticated user still belongs to an active organization.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database.session import get_db
from app.models.user import User


security = HTTPBearer(auto_error=True)


def _unauthorized(detail: str = "Invalid authentication credentials.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Validate the bearer token and return an active authenticated user."""

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise _unauthorized() from exc

    if not payload:
        raise _unauthorized()

    user_id = payload.get("user_id")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise _unauthorized() from exc

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise _unauthorized("User not found.")

    organization = user.organization

    if organization is None:
        raise _unauthorized("User organization not found.")

    if hasattr(organization, "is_active") and not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive.",
        )

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user
