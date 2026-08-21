"""Public company onboarding API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import OnboardingService
from app.utils.response import ApiResponse


router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
)


@router.post("/register-company", status_code=201)
def register_company(
    request: OnboardingRequest,
    db: Session = Depends(get_db),
):
    """Create a new SaaS tenant and its initial AI receptionist."""

    service = OnboardingService(db)

    try:
        organization, admin, agent = service.onboard(request)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return ApiResponse.success(
        data=OnboardingResponse(
            organization_id=organization.id,
            admin_user_id=admin.id,
            agent_id=agent.id,
            public_slug=agent.public_slug,
        ),
        message="Company registered successfully.",
    )
