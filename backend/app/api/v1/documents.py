"""
Document upload API.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.knowledge_repository import (
    KnowledgeRepository,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.agent_service import AgentService
from app.tenants.resolver import (
    get_current_tenant,
)
from app.tenants.tenant_context import (
    TenantContext,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
)
async def upload_document(
    file: UploadFile = File(...),
    category: str = "general",
    agent_id: int | None = None,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(
        get_current_tenant
    ),
):

    repository = KnowledgeRepository(
        db
    )

    if agent_id is not None and not AgentService(db).get(
        agent_id,
        tenant.organization_id,
    ):
        raise HTTPException(status_code=404, detail="AI receptionist not found.")

    service = DocumentService(
        knowledge_repository=repository
    )

    try:

        knowledge = (
            await service.process_upload(
                file=file,
                organization_id=(
                    tenant.organization_id
                ),
                category=category,
                agent_id=agent_id,
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    db.commit()

    db.refresh(
        knowledge
    )

    return {
        "success": True,
        "message": (
            "Document uploaded and "
            "embedded successfully."
        ),
        "data": {
            "id": knowledge.id,
            "title": knowledge.title,
            "category": knowledge.category,
            "source": knowledge.source,
            "uuid": str(
                knowledge.uuid
            ),
        },
    }
