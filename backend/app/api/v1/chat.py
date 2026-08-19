"""
AI Receptionist chat API.
"""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.chat import ChatRequest
from app.schemas.chat import ChatResponse
from app.services.chat_service import ChatService
from app.tenants.resolver import get_current_tenant
from app.tenants.tenant_context import TenantContext


router = APIRouter(
    prefix="/chat",
    tags=["AI Receptionist"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    service = ChatService(db)

    session_id, response = (
        await service.generate_response(
            message=request.message,
            organization_id=tenant.organization_id,
            user_id=tenant.user_id,
            session_id=request.session_id,
        )
    )

    return ChatResponse(
        session_id=session_id,
        response=response,
    )