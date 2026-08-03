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


class UpdateFindingRequest(BaseSchema):
    status: FindingStatus | None = None
    severity: FindingSeverity | None = None
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=10000)
