import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.ai.repositories import conversation_repository as conversation_repo
from app.ai.schemas import AIChatRequest, AIChatResponse, ConversationDetail, ConversationSummary, MessageResponse
from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.services.ai.service import ai_service
from app.users.models import User

router = APIRouter()


@router.post("/chat")
def chat_with_assistant(
    body: AIChatRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.AI_USE)),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    result: AIChatResponse = ai_service.chat(
        db,
        membership,
        user_id=current_user.id,
        request=body,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.AI_USE)),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    conversations = conversation_repo.list_conversations_for_user(
        db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
    )
    items = [
        ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        ).model_dump(mode="json")
        for conversation in conversations
    ]
    return success_response(data={"items": items, "total": len(items)})


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.AI_USE)),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    conversation = conversation_repo.get_conversation_for_user(
        db,
        organization_id=membership.organization_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise NotFoundError("Conversation")

    detail = ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                model=message.model,
                token_count=message.token_count,
                created_at=message.created_at,
            )
            for message in conversation.messages
        ],
    )
    return success_response(data=detail.model_dump(mode="json"))
