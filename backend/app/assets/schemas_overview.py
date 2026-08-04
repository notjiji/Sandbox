from pydantic import Field

from app.assets.schemas import AssetSummary
from app.audit.schemas import AuditLogSummary
from app.findings.schemas import FindingSummary
from app.organizations.schemas_overview import RecentReportSummary, RecentScanSummary, UsagePlaceholder
from app.risk.schemas import AssetRiskResponse, RiskTrendPoint
from app.scans.schemas import ScanSummary
from app.shared.schemas.base import BaseSchema


class AssetStats(BaseSchema):
    scans: int = 0
    open_findings: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    reports: int = 0


class AssetOverview(BaseSchema):
    asset: AssetSummary
    stats: AssetStats
    risk: AssetRiskResponse
    scan_trend: list[RiskTrendPoint] = Field(default_factory=list)
    recent_scans: list[ScanSummary] = Field(default_factory=list)
    top_findings: list[FindingSummary] = Field(default_factory=list)
    recent_reports: list[RecentReportSummary] = Field(default_factory=list)
    recent_activity: list[AuditLogSummary] = Field(default_factory=list)
    ai_summary: UsagePlaceholder = Field(
        default_factory=lambda: UsagePlaceholder(
            label="AI Summary",
            value="Coming soon",
            available=False,
        )
    )
