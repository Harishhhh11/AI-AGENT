"""
Permission dependency.
"""

from fastapi import Depends
from fastapi import HTTPException

from app.auth.dependencies import get_current_user


def require_permission(
    permission: str,
):

    def checker(
        current_user=Depends(
            get_current_user
        ),
    ):

        permissions = current_user.get(
            "permissions",
            [],
        )

        is_superuser = current_user.get(
            "is_superuser",
            False,
        )

        if is_superuser:
            return current_user

        if permission not in permissions:

            raise HTTPException(
                status_code=403,
                detail="Permission denied.",
            )

        return current_user

    return checker