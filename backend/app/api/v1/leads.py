"""
Lead management API.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.lead import LeadResponse
from app.schemas.lead import LeadUpdate
from app.services.lead_service import LeadService


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


@router.get(
    "",
    response_model=list[LeadResponse],
)
def get_leads(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = LeadService(db)

    if status:

        return service.get_leads_by_status(
            organization_id=current_user.organization_id,
            status=status,
        )

    return service.get_all_leads(
        organization_id=current_user.organization_id
    )


@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = LeadService(db)

    lead = service.get_lead(
        lead_id=lead_id,
        organization_id=current_user.organization_id,
    )

    if lead is None:

        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    return lead


@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
)
def update_lead(
    lead_id: int,
    data: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = LeadService(db)

    try:

        lead = service.update_lead(
            lead_id=lead_id,
            organization_id=current_user.organization_id,
            name=data.name,
            phone=data.phone,
            email=data.email,
            interest=data.interest,
            preferred_mode=data.preferred_mode,
            preferred_time=data.preferred_time,
            notes=data.notes,
            status=data.status,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if lead is None:

        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    return lead


@router.delete(
    "/{lead_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    service = LeadService(db)

    deleted = service.delete_lead(
        lead_id=lead_id,
        organization_id=current_user.organization_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
