from datetime import datetime

from app.shared.schemas.base import BaseSchema


class AuditLogSummary(BaseSchema):
    id: str
    action: str
    user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    details: dict | None = None
    created_at: datetime


class AuditLogListResponse(BaseSchema):
    items: list[AuditLogSummary]
    total: int
