from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.organization_service import OrganizationService


def get_organization_service(
    db: Session = Depends(get_db),
) -> OrganizationService:
    """
    Dependency that provides an OrganizationService.
    """
    return OrganizationService(db)


OrganizationServiceDep = Annotated[
    OrganizationService,
    Depends(get_organization_service),
]