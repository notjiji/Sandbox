"""Conversation persistence for the AI assistant."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.ai.repositories import conversation_repository as repo
from app.ai.models import AIConversation


def get_or_create_conversation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    title: str | None = None,
) -> AIConversation:
    if conversation_id is not None:
        conversation = repo.get_conversation_for_user(
            db,
            organization_id=organization_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("Conversation")
        return conversation
    return repo.create_conversation(
        db,
        organization_id=organization_id,
        user_id=user_id,
        title=title,
    )


def append_message(
    db: Session,
    *,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    model: str | None = None,
    token_count: int | None = None,
) -> None:
    repo.add_message(
        db,
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model,
        token_count=token_count,
    )


def list_user_conversations(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[AIConversation]:
    return repo.list_conversations_for_user(
        db,
        organization_id=organization_id,
        user_id=user_id,
        limit=limit,
    )
