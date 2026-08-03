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
    recommendation_id: str | None = None
    asset_id: str
    asset_criticality: str | None = None


class ProjectRiskResponse(BaseSchema):
    project_id: str
    total_risk: float = Field(description="Sum of finding risk points")
    security_score: float = Field(description="max(0, 100 - total_risk)")
    grade: str
    risk_level: str
    open_findings: int
    breakdown: SeverityBreakdown
    top_issues: list[PrioritizedFinding] = Field(default_factory=list)
    calculated_at: datetime | None = None


class AssetRiskResponse(BaseSchema):
    asset_id: str
    scanned: bool = False
    scan_id: str | None = None
    total_risk: float | None = None
    score: float | None = Field(default=None, description="Security score; null when not scanned")
    grade: str | None = Field(default=None, description="Letter grade; null when not scanned")
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    calculated_at: datetime | None = None


def unscanned_asset_risk(*, asset_id: str) -> AssetRiskResponse:
    return AssetRiskResponse(asset_id=asset_id, scanned=False)


class OrganizationRiskResponse(BaseSchema):
    organization_id: str
    overall_score: float | None = Field(
        default=None,
        description="Average security score across scanned assets only",
    )
    total_risk: float | None = None
    grade: str | None = None
    risk_level: str | None = None
    trend: str = "stable"
    scanned_assets: int = 0
    unscanned_assets: int = 0
    asset_scores: list[AssetRiskResponse] = Field(default_factory=list)
    updated_at: datetime | None = None


class RiskTrendPoint(BaseSchema):
    date: datetime
    security_score: float
    grade: str
    total_risk: float


class DashboardMetrics(BaseSchema):
    overall_security_score: float | None = None
    organization_grade: str | None = None
    risk_level: str | None = None
    trend: str
    total_findings: int
    critical_findings: int
    high_findings: int
    assets_at_risk: int
    unscanned_assets: int = 0
    most_common_issue: str | None = None
    average_days_between_scans: float | None = None
    findings_by_plugin: dict[str, int] = Field(default_factory=dict)
    findings_by_asset_type: dict[str, int] = Field(default_factory=dict)
    risk_trend: list[RiskTrendPoint] = Field(default_factory=list)
