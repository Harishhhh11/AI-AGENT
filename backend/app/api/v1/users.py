"""
User management API.

All user operations are restricted to the
authenticated user's organization.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.auth.authorization import require_permission
from app.auth.permissions import Permission
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse
from app.schemas.user import UserRoleUpdate
from app.schemas.user import UserUpdate
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def _serialize_user(user: User) -> UserResponse:
    """Serialize a user together with organization-scoped role IDs."""

    response = UserResponse.model_validate(user)
    response.role_ids = [role.id for role in (user.roles or [])]
    return response


@router.post(
    "",
    status_code=201,
)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_CREATE)
    ),
):

    service = UserService(db)

    try:

        user = service.create_user(
            request,
            current_user.organization_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "data": _serialize_user(user),
        "message": "User created successfully.",
    }


@router.get("")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_READ)
    ),
):

    service = UserService(db)

    users = service.get_all_users(
        current_user.organization_id
    )

    return {
        "data": [
            _serialize_user(user)
            for user in users
        ],
        "message": "Users fetched successfully.",
    }


@router.get(
    "/{user_id}",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_READ)
    ),
):

    service = UserService(db)

    user = service.get_user(
        user_id,
        current_user.organization_id,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return {
        "data": _serialize_user(user),
        "message": "User fetched successfully.",
    }


@router.put(
    "/{user_id}",
)
def update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_UPDATE)
    ),
):

    service = UserService(db)

    user = service.update_user(
        user_id,
        request,
        current_user.organization_id,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return {
        "data": _serialize_user(user),
        "message": "User updated successfully.",
    }


@router.delete(
    "/{user_id}",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_DELETE)
    ),
):

    service = UserService(db)

    deleted = service.delete_user(
        user_id,
        current_user.organization_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return {
        "message": "User deleted successfully.",
    }


@router.post(
    "/{user_id}/roles",
    status_code=status.HTTP_200_OK,
)
def assign_role(
    user_id: int,
    request: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_UPDATE)
    ),
):

    try:
        user = UserService(db).assign_role(
            user_id=user_id,
            role_id=request.role_id,
            organization_id=current_user.organization_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User or role not found.",
        )

    return {
        "data": _serialize_user(user),
        "message": "Role assigned successfully.",
    }


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_200_OK,
)
def remove_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.USER_UPDATE)
    ),
):

    user = UserService(db).remove_role(
        user_id=user_id,
        role_id=role_id,
        organization_id=current_user.organization_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User or role not found.",
        )

    return {
        "data": _serialize_user(user),
        "message": "Role removed successfully.",
    }
