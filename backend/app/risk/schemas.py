from pydantic import Field

from app.schemas.base import BaseSchema


class SeverityBreakdown(BaseSchema):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ProjectRiskResponse(BaseSchema):
    project_id: str
    score: float = Field(description="Weighted risk score from open findings")
    open_findings: int
    breakdown: SeverityBreakdown
