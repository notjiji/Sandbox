from pydantic import Field

from app.models.finding import FindingSeverity, FindingStatus
from app.schemas.base import BaseSchema


class FindingSummary(BaseSchema):
    id: str
    project_id: str
    scan_id: str
    asset_id: str
    title: str
    description: str | None = None
    severity: FindingSeverity
    status: FindingStatus


class FindingListResponse(BaseSchema):
    items: list[FindingSummary]
    total: int


class UpdateFindingRequest(BaseSchema):
    status: FindingStatus | None = None
    severity: FindingSeverity | None = None
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=10000)
