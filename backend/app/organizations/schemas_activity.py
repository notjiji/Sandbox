from datetime import datetime

from pydantic import Field

from app.shared.schemas.base import BaseSchema


class ActivityActor(BaseSchema):
    id: str | None = None
    name: str
    email: str | None = None


class ActivityEvent(BaseSchema):
    id: str
    message: str
    category: str
    action: str
    actor: ActivityActor | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    severity: str = "info"
    href: str | None = None
    created_at: datetime


class OrganizationActivityResponse(BaseSchema):
    items: list[ActivityEvent] = Field(default_factory=list)
    total: int
    page: int
    limit: int
