"""Integration catalog API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.integrations import IntegrationCatalog
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("", response_model=IntegrationCatalog)
def get_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntegrationCatalog:
    del db, current_user
    return IntegrationService().catalog()