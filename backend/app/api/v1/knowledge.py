"""
Knowledge base API.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.knowledge import KnowledgeCreate
from app.schemas.knowledge import KnowledgeResponse
from app.schemas.knowledge import KnowledgeUpdate
from app.services.agent_service import AgentService
from app.services.knowledge_service import KnowledgeService


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


@router.post(
    "",
    response_model=KnowledgeResponse,
)
def create_knowledge(
    data: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = KnowledgeService(db)

    if data.agent_id is not None and not AgentService(db).get(
        data.agent_id,
        current_user.organization_id,
    ):
        raise HTTPException(status_code=404, detail="AI receptionist not found.")

    return service.create(
        organization_id=current_user.organization_id,
        title=data.title,
        content=data.content,
        source=data.source,
        category=data.category,
        agent_id=data.agent_id,
    )


@router.get(
    "",
    response_model=list[KnowledgeResponse],
)
def get_knowledge(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = KnowledgeService(db)

    return service.get_all(
        organization_id=current_user.organization_id
    )


@router.get(
    "/{knowledge_id}",
    response_model=KnowledgeResponse,
)
def get_knowledge_by_id(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = KnowledgeService(db)

    item = service.get_by_id(
        knowledge_id=knowledge_id,
        organization_id=current_user.organization_id,
    )

    if item is None:

        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found.",
        )

    return item


@router.patch(
    "/{knowledge_id}",
    response_model=KnowledgeResponse,
)
def update_knowledge(
    knowledge_id: int,
    data: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = KnowledgeService(db)

    item = service.update(
        knowledge_id=knowledge_id,
        organization_id=current_user.organization_id,
        title=data.title,
        content=data.content,
        source=data.source,
        category=data.category,
        is_active=data.is_active,
    )

    if item is None:

        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found.",
        )

    return item


@router.delete(
    "/{knowledge_id}",
)
def delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = KnowledgeService(db)

    deleted = service.delete(
        knowledge_id=knowledge_id,
        organization_id=current_user.organization_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found.",
        )

    return {
        "message": "Knowledge deleted successfully."
    }


@router.post(
    "/{knowledge_id}/deactivate",
    response_model=KnowledgeResponse,
)
def deactivate_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    service = KnowledgeService(db)

    item = service.deactivate(
        knowledge_id=knowledge_id,
        organization_id=current_user.organization_id,
    )

    if item is None:

        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found.",
        )

    return item
