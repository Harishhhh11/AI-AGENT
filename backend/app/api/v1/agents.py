"""Admin and public APIs for publishable AI receptionists."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.authorization import require_permission
from app.database.session import get_db
from app.models.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentKnowledgeUpdate,
    AgentResponse,
    AgentUpdate,
    PublicAgentResponse,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.knowledge import KnowledgeResponse
from app.services.agent_service import AgentService
from app.services.chat_service import ChatService
from app.tenants.resolver import get_current_tenant
from app.tenants.tenant_context import TenantContext


router = APIRouter(tags=["AI Receptionists"])


def _require_permission(user: User, permission: str) -> User:
    """Centralize permission checks without changing the dependency contract."""
    require_permission(user, permission)
    return user


def _agent_response(agent) -> AgentResponse:
    data = AgentResponse.model_validate(agent)
    data.knowledge_item_ids = [
        int(item.id)
        for item in (agent.knowledge_items or [])
        if getattr(item, "is_active", False) and item.id is not None
    ]
    return data


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:create")
    try:
        return _agent_response(AgentService(db).create(current_user.organization_id, data))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/agents", response_model=list[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:read")
    return [_agent_response(agent) for agent in AgentService(db).get_all(current_user.organization_id)]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:read")
    agent = AgentService(db).get(agent_id, current_user.organization_id)
    if not agent:
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    return _agent_response(agent)


@router.get("/agents/{agent_id}/knowledge", response_model=list[KnowledgeResponse])
def get_agent_knowledge(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:read")
    items = AgentService(db).get_knowledge(agent_id, current_user.organization_id)
    if items is None:
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    return items


@router.put("/agents/{agent_id}/knowledge", response_model=AgentResponse)
def update_agent_knowledge(
    agent_id: int,
    data: AgentKnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:update")
    try:
        agent = AgentService(db).set_knowledge(agent_id, current_user.organization_id, data.knowledge_item_ids)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not agent:
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    return _agent_response(agent)


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:update")
    agent = AgentService(db).update(agent_id, current_user.organization_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    return _agent_response(agent)


@router.post("/agents/{agent_id}/publish", response_model=AgentResponse)
def publish_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:update")
    try:
        agent = AgentService(db).set_published(agent_id, current_user.organization_id, True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not agent:
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    return _agent_response(agent)


@router.post("/agents/{agent_id}/unpublish", response_model=AgentResponse)
def unpublish_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant),
):
    _require_permission(current_user, "agent:update")
    agent = AgentService(db).set_published(agent_id, current_user.organization_id, False)
    if not agent:
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    return _agent_response(agent)


@router.get("/public/agents/{public_slug}", response_model=PublicAgentResponse)
def get_public_agent(public_slug: str, db: Session = Depends(get_db)):
    agent = AgentService(db).get_public(public_slug)
    if not agent:
        raise HTTPException(status_code=404, detail="This AI receptionist is unavailable.")
    return PublicAgentResponse.model_validate(agent)


@router.post("/public/agents/{public_slug}/chat", response_model=ChatResponse)
async def public_agent_chat(
    public_slug: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    agent = AgentService(db).get_public(public_slug)
    if not agent:
        raise HTTPException(status_code=404, detail="This AI receptionist is unavailable.")
    session_id, response = await ChatService(db).generate_response(
        message=request.message,
        organization_id=agent.organization_id,
        agent_id=agent.id,
        agent_instructions=agent.system_instructions,
        session_id=request.session_id,
    )
    return ChatResponse(session_id=session_id, response=response)
