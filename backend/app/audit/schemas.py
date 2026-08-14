from datetime import datetime

from pydantic import Field

from app.shared.schemas.base import BaseSchema


class AuditLogSummary(BaseSchema):
    id: str
    action: str
    user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    severity: str = "info"
    details: dict | None = None
    created_at: datetime


class AuditLogListResponse(BaseSchema):
    items: list[AuditLogSummary]
    total: int


class AuditLogRecord(BaseSchema):
    id: str
    organization_id: str | None = None
    user_id: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    severity: str
    details: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime


class AuditLogSearchResponse(BaseSchema):
    items: list[AuditLogRecord] = Field(default_factory=list)
    total: int
    page: int
    limit: int
