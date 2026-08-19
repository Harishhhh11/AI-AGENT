"""
Organization API.

Organization creation is used during onboarding.
Existing organization data requires authentication
and tenant ownership.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.exceptions.organization import (
    OrganizationAlreadyExistsException,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
)
from app.services.organization_service import (
    OrganizationService,
)
from app.tenants.resolver import get_current_tenant
from app.tenants.tenant_context import TenantContext
from app.utils.response import ApiResponse


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


@router.post(
    "",
    status_code=201,
)
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
):

    service = OrganizationService(db)

    result = service.create_organization(
        organization
    )

    return ApiResponse.success(
        data=OrganizationResponse.model_validate(
            result
        ),
        message="Organization created successfully.",
    )


@router.get(
    "/me",
)
def get_my_organization(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = OrganizationService(db)

    organization = service.get_organization(
        tenant.organization_id
    )

    if organization is None:

        raise HTTPException(
            status_code=404,
            detail="Organization not found.",
        )

    return ApiResponse.success(
        data=OrganizationResponse.model_validate(
            organization
        ),
        message="Organization fetched successfully.",
    )


@router.get(
    "/{organization_id}",
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    if (
        organization_id
        != tenant.organization_id
    ):

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization.",
        )

    service = OrganizationService(db)

    organization = service.get_organization(
        organization_id
    )

    if organization is None:

        raise HTTPException(
            status_code=404,
            detail="Organization not found.",
        )

    return ApiResponse.success(
        data=OrganizationResponse.model_validate(
            organization
        ),
        message="Organization fetched successfully.",
    )


@router.put(
    "/{organization_id}",
)
def update_organization(
    organization_id: int,
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    if (
        organization_id
        != tenant.organization_id
    ):

        raise HTTPException(
            status_code=403,
            detail="You cannot modify another organization.",
        )

    service = OrganizationService(db)

    try:

        result = service.update_organization(
            organization_id,
            organization,
        )

    except OrganizationAlreadyExistsException:

        raise

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Organization not found.",
        )

    return ApiResponse.success(
        data=OrganizationResponse.model_validate(
            result
        ),
        message="Organization updated successfully.",
    )


@router.delete(
    "/{organization_id}",
)
def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    if (
        organization_id
        != tenant.organization_id
    ):

        raise HTTPException(
            status_code=403,
            detail="You cannot delete another organization.",
        )

    service = OrganizationService(db)

    deleted = service.delete_organization(
        organization_id
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Organization not found.",
        )

    return ApiResponse.success(
        message="Organization deleted successfully.",
    )