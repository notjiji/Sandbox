"""AI assistant API schemas."""

import uuid
from datetime import datetime

from app.services.ai.models import AICapability, AIChatRequest, AIChatResponse, AIResponsePayload
from app.shared.schemas.base import BaseSchema


class ConversationSummary(BaseSchema):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseSchema):
    id: uuid.UUID
    role: str
    content: str
    model: str | None = None
    token_count: int | None = None
    created_at: datetime


class ConversationDetail(BaseSchema):
    id: uuid.UUID
    title: str | None
    messages: list[MessageResponse]
    created_at: datetime
    updated_at: datetime


__all__ = [
    "AICapability",
    "AIChatRequest",
    "AIChatResponse",
    "AIResponsePayload",
    "ConversationSummary",
    "ConversationDetail",
    "MessageResponse",
]
