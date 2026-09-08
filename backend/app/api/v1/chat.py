"""Authenticated AI receptionist chat API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService
from app.services.chat_service import ChatService
from app.tenants.resolver import get_current_tenant
from app.tenants.tenant_context import TenantContext


router = APIRouter(prefix="/chat", tags=["AI Receptionist"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    agent_id = request.agent_id
    agent_instructions = None

    if agent_id is not None:
        agent = AgentService(db).get(agent_id, tenant.organization_id)
        if not agent or not agent.is_active:
            raise HTTPException(status_code=404, detail="AI receptionist not found.")
        agent_instructions = agent.system_instructions

    session_id, response = await ChatService(db).generate_response(
        message=request.message,
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        session_id=request.session_id,
        agent_id=agent_id,
        agent_instructions=agent_instructions,
    )

    return ChatResponse(session_id=session_id, response=response)
