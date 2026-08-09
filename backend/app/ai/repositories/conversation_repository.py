import uuid

from sqlalchemy.orm import Session, joinedload

from app.ai.models import AIConversation, AIMessage


def create_conversation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str | None = None,
) -> AIConversation:
    conversation = AIConversation(
        organization_id=organization_id,
        user_id=user_id,
        title=title,
    )
    db.add(conversation)
    db.flush()
    return conversation


def get_conversation_for_user(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> AIConversation | None:
    return (
        db.query(AIConversation)
        .options(joinedload(AIConversation.messages))
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.organization_id == organization_id,
            AIConversation.user_id == user_id,
        )
        .first()
    )


def list_conversations_for_user(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[AIConversation]:
    return (
        db.query(AIConversation)
        .filter(
            AIConversation.organization_id == organization_id,
            AIConversation.user_id == user_id,
        )
        .order_by(AIConversation.updated_at.desc())
        .limit(limit)
        .all()
    )


def add_message(
    db: Session,
    *,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    model: str | None = None,
    token_count: int | None = None,
) -> AIMessage:
    message = AIMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model,
        token_count=token_count,
    )
    db.add(message)
    db.flush()
    return message


def delete_conversation(
    db: Session,
    conversation: AIConversation,
) -> None:
    db.delete(conversation)
    db.flush()
