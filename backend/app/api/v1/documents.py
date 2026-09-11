"""Document upload API."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.agent_service import AgentService
from app.services.document_service import DocumentService
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
        records = await DocumentService(KnowledgeRepository(db)).process_upload(
            file=file,
            organization_id=tenant.organization_id,
            category=category.strip() or "general",
            agent_id=agent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    for record in records:
        db.refresh(record)

    primary = records[0]
    return {
        "success": True,
        "message": (
            "Document uploaded and indexed successfully."
            if len(records) == 1
            else f"Document uploaded and split into {len(records)} indexed sections."
        ),
        "data": {
            "id": primary.id,
            "title": primary.title,
            "category": primary.category,
            "source": primary.source,
            "uuid": str(primary.uuid),
            "agent_id": primary.agent_id,
            "chunks_created": len(records),
            "chunks": [
                {"id": record.id, "title": record.title, "uuid": str(record.uuid)}
                for record in records
            ],
        },
    }
