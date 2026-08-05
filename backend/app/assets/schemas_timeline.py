from pydantic import Field

from app.organizations.schemas_activity import ActivityEvent
from app.shared.schemas.base import BaseSchema


class AssetTimelineResponse(BaseSchema):
    items: list[ActivityEvent] = Field(default_factory=list)
    total: int = 0
