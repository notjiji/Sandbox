from datetime import datetime

from pydantic import Field

from app.findings.enums import FindingSeverity, FindingStatus
from app.shared.schemas.base import BaseSchema


class FindingSummary(BaseSchema):
    id: str
    project_id: str
    scan_id: str
    asset_id: str
    plugin: str | None = None
    finding_code: str | None = None
    check_status: str | None = None
    recommendation_id: str | None = None
    title: str
    description: str | None = None
    severity: FindingSeverity
    risk_score: float = 0.0
    status: FindingStatus
    evidence: str | None = None
    recommendation: str | None = None
    references: list[str] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)
    confidence: float | None = None
    detected_at: datetime | None = None


class FindingListResponse(BaseSchema):
    items: list[FindingSummary]
    total: int
    page: int = 1
    limit: int = 20


class FindingListQuery(BaseSchema):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status_group: str | None = Field(
        default=None,
        description="open | resolved | ignored",
    )
    status: FindingStatus | None = None
    severity: FindingSeverity | None = None
    search: str | None = Field(default=None, max_length=255)
    sort: str = Field(default="risk_score", description="risk_score | severity | title | created_at")
    order: str = Field(default="desc", description="asc | desc")


class UpdateFindingRequest(BaseSchema):
    status: FindingStatus | None = None
    severity: FindingSeverity | None = None
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=10000)
