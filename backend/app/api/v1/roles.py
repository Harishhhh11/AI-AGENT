"""Organization-scoped role management API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.authorization import require_permission
from app.auth.permissions import Permission
from app.database.session import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.role_service import RoleService


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.ROLE_CREATE)
    ),
):
    try:
        return RoleService(db).create(
            current_user.organization_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[RoleResponse],
)
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.ROLE_READ)
    ),
):
    return RoleService(db).get_all(
        current_user.organization_id,
    )


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.ROLE_READ)
    ),
):
    role = RoleService(db).get(
        role_id,
        current_user.organization_id,
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    return role


@router.patch(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.ROLE_UPDATE)
    ),
):
    role = RoleService(db).update(
        role_id,
        current_user.organization_id,
        data,
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(Permission.ROLE_DELETE)
    ),
):
    deleted = RoleService(db).delete(
        role_id,
        current_user.organization_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found.")
    return None
