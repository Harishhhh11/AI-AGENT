"""
Conversation management API.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationResponse,
)
from app.schemas.conversation import (
    ConversationStatusUpdate,
)
from app.schemas.conversation import (
    MessageResponse,
)
from app.services.conversation_service import (
    ConversationService,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def get_conversations(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Get conversations belonging to the
    authenticated user's organization.
    """

    service = ConversationService(db)

    if status:
        return (
            service.get_conversations_by_status(
                organization_id=(
                    current_user.organization_id
                ),
                status=status,
            )
        )

    return service.get_all_conversations(
        organization_id=(
            current_user.organization_id
        )
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Get one conversation belonging to the
    authenticated user's organization.
    """

    service = ConversationService(db)

    conversation = service.get_conversation(
        conversation_id=conversation_id,
        organization_id=(
            current_user.organization_id
        ),
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Get messages for a conversation after
    verifying that the conversation belongs
    to the authenticated user's organization.
    """

    service = ConversationService(db)

    conversation = service.get_conversation(
        conversation_id=conversation_id,
        organization_id=(
            current_user.organization_id
        ),
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return service.get_messages(
        conversation_id
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def update_conversation_status(
    conversation_id: int,
    data: ConversationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Update conversation status.
    """

    service = ConversationService(db)

    try:
        conversation = (
            service.update_status(
                conversation_id=conversation_id,
                organization_id=(
                    current_user.organization_id
                ),
                status=data.status,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation