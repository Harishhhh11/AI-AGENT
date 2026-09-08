"""Knowledge base API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.knowledge import KnowledgeCreate, KnowledgeResponse, KnowledgeUpdate
from app.services.agent_service import AgentService
from app.services.knowledge_service import KnowledgeService


router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("", response_model=KnowledgeResponse)
def create_knowledge(
    data: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.agent_id is not None and not AgentService(db).get(data.agent_id, current_user.organization_id):
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    try:
        return KnowledgeService(db).create(
            organization_id=current_user.organization_id,
            title=data.title,
            content=data.content,
            source=data.source,
            category=data.category,
            agent_id=data.agent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[KnowledgeResponse])
def get_knowledge(
    agent_id: int | None = None,
    scope: str = "all",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if scope not in {"all", "shared", "agent", "available"}:
        raise HTTPException(status_code=400, detail="Invalid knowledge scope.")
    if agent_id is not None and not AgentService(db).get(agent_id, current_user.organization_id):
        raise HTTPException(status_code=404, detail="AI receptionist not found.")
    try:
        return KnowledgeService(db).get_all(
            organization_id=current_user.organization_id,
            agent_id=agent_id,
            scope=scope,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
def get_knowledge_by_id(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = KnowledgeService(db).get_by_id(knowledge_id, current_user.organization_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge record not found.")
    return item


@router.patch("/{knowledge_id}", response_model=KnowledgeResponse)
def update_knowledge(
    knowledge_id: int,
    data: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_values = data.model_dump(exclude_unset=True)
    if "agent_id" in update_values:
        target_agent_id = update_values["agent_id"]
        if target_agent_id is not None and not AgentService(db).get(target_agent_id, current_user.organization_id):
            raise HTTPException(status_code=404, detail="AI receptionist not found.")

    service = KnowledgeService(db)
    kwargs = {
        "knowledge_id": knowledge_id,
        "organization_id": current_user.organization_id,
        "title": data.title,
        "content": data.content,
        "source": data.source,
        "category": data.category,
        "is_active": data.is_active,
    }
    if "agent_id" in update_values:
        kwargs["agent_id"] = update_values["agent_id"]

    try:
        item = service.update(**kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge record not found.")
    return item


@router.delete("/{knowledge_id}")
def delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not KnowledgeService(db).delete(knowledge_id, current_user.organization_id):
        raise HTTPException(status_code=404, detail="Knowledge record not found.")
    return {"message": "Knowledge deleted successfully."}


@router.post("/{knowledge_id}/deactivate", response_model=KnowledgeResponse)
def deactivate_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = KnowledgeService(db).deactivate(knowledge_id, current_user.organization_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge record not found.")
    return item
