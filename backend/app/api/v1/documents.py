"""Document upload API."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.document_service import DocumentService
from app.services.agent_service import AgentService
from app.tenants.resolver import get_current_tenant
from app.tenants.tenant_context import TenantContext


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general"),
    agent_id: int | None = Form(None),
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    if agent_id is not None and not AgentService(db).get(agent_id, tenant.organization_id):
        raise HTTPException(status_code=404, detail="AI receptionist not found.")

    try:
        knowledge = await DocumentService(KnowledgeRepository(db)).process_upload(
            file=file,
            organization_id=tenant.organization_id,
            category=category.strip() or "general",
            agent_id=agent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    db.refresh(knowledge)
    return {
        "success": True,
        "message": "Document uploaded and indexed successfully.",
        "data": {
            "id": knowledge.id,
            "title": knowledge.title,
            "category": knowledge.category,
            "source": knowledge.source,
            "uuid": str(knowledge.uuid),
            "agent_id": knowledge.agent_id,
            "chunks_created": 1,
            "chunks": [{"id": knowledge.id, "title": knowledge.title, "uuid": str(knowledge.uuid)}],
        },
    }
