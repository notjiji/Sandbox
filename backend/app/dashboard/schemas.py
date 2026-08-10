from datetime import datetime

from pydantic import Field

from app.risk.schemas import RiskTrendPoint, SeverityBreakdown
from app.shared.schemas.base import BaseSchema


class DashboardScore(BaseSchema):
    current: float | None = None
    previous: float | None = None
    change: float | None = None
    grade: str | None = None
    trend: str = "stable"


class DashboardAssetsSummary(BaseSchema):
    total: int = 0
    websites: int = 0
    domains: int = 0
    ips: int = 0
    servers: int = 0


class DashboardLastScan(BaseSchema):
    status: str | None = None
    timestamp: datetime | None = None
    scan_id: str | None = None
    project_id: str | None = None
    asset_id: str | None = None
    asset_name: str | None = None


class DashboardCriticalFinding(BaseSchema):
    finding_id: str
    finding_code: str
    title: str
    severity: str
    risk_score: float
    asset_id: str
    asset_name: str
    project_id: str


class DashboardTopAsset(BaseSchema):
    asset_id: str
    asset_name: str
    project_id: str
    score: float | None = None
    grade: str | None = None
    scanned: bool = False


class DashboardUpcomingScan(BaseSchema):
    schedule_id: str
    asset_id: str
    asset_name: str
    project_id: str
    scan_type: str
    preset: str
    next_run_at: datetime


class DashboardOverviewResponse(BaseSchema):
    score: DashboardScore
    assets: DashboardAssetsSummary
    findings: SeverityBreakdown
    last_scan: DashboardLastScan
    primary_project_id: str | None = None
    scanned_assets: int = 0
    unscanned_assets: int = 0
    assets_at_risk: int = 0
    trend: str = "stable"


class DashboardFindingsSummaryResponse(BaseSchema):
    breakdown: SeverityBreakdown
    top_findings: list[DashboardCriticalFinding] = Field(default_factory=list)


class DashboardRiskTrendResponse(BaseSchema):
    history: list[RiskTrendPoint] = Field(default_factory=list)


class DashboardTopAssetsResponse(BaseSchema):
    items: list[DashboardTopAsset] = Field(default_factory=list)


class DashboardActivityResponse(BaseSchema):
    items: list[dict] = Field(default_factory=list)
    total: int = 0


class DashboardUpcomingScansResponse(BaseSchema):
    items: list[DashboardUpcomingScan] = Field(default_factory=list)
