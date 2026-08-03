from datetime import datetime

from pydantic import Field

from app.findings.enums import FindingSeverity
from app.schemas.base import BaseSchema


class SeverityBreakdown(BaseSchema):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class PrioritizedFinding(BaseSchema):
    finding_id: str
    finding_code: str
    title: str
    severity: FindingSeverity
    risk_score: float
    weighted_score: float
    asset_id: str


class ProjectRiskResponse(BaseSchema):
    project_id: str
    score: float = Field(description="Rule-based risk score from open findings")
    open_findings: int
    breakdown: SeverityBreakdown
    top_issues: list[PrioritizedFinding] = Field(default_factory=list)
    calculated_at: datetime | None = None
