"""
User management API.

All user operations are restricted to the
authenticated user's organization.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse
from app.schemas.user import UserUpdate
from app.services.user_service import UserService
from app.tenants.resolver import get_current_tenant
from app.tenants.tenant_context import TenantContext
from app.utils.response import ApiResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    status_code=201,
)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = UserService(db)

    try:

        user = service.create_user(
            request,
            tenant.organization_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="User created successfully.",
    )


@router.get("")
def get_users(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = UserService(db)

    users = service.get_all_users(
        tenant.organization_id
    )

    return ApiResponse.success(
        data=[
            UserResponse.model_validate(user)
            for user in users
        ],
        message="Users fetched successfully.",
    )


@router.get(
    "/{user_id}",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = UserService(db)

    user = service.get_user(
        user_id,
        tenant.organization_id,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="User fetched successfully.",
    )


@router.put(
    "/{user_id}",
)
def update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = UserService(db)

    user = service.update_user(
        user_id,
        request,
        tenant.organization_id,
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="User updated successfully.",
    )


@router.delete(
    "/{user_id}",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = UserService(db)

    deleted = service.delete_user(
        user_id,
        tenant.organization_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return ApiResponse.success(
        message="User deleted successfully.",
    )