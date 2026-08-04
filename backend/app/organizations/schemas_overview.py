from datetime import datetime

from pydantic import Field

from app.audit.schemas import AuditLogSummary
from app.reports.enums import ReportStatus
from app.risk.schemas import DashboardMetrics
from app.scans.enums import ScanStatus, ScanType
from app.shared.schemas.base import BaseSchema


class OrganizationStats(BaseSchema):
    projects: int = 0
    assets: int = 0
    members: int = 0
    scans: int = 0
    open_findings: int = 0
    total_findings: int = 0
    reports: int = 0


class RecentScanSummary(BaseSchema):
    id: str
    project_id: str
    asset_id: str
    status: ScanStatus
    scan_type: ScanType
    created_at: datetime


class RecentReportSummary(BaseSchema):
    id: str
    project_id: str
    name: str
    status: ReportStatus
    created_at: datetime


class UsagePlaceholder(BaseSchema):
    label: str
    value: str
    available: bool = False


class OrganizationOverview(BaseSchema):
    stats: OrganizationStats
    security: DashboardMetrics
    recent_scans: list[RecentScanSummary] = Field(default_factory=list)
    recent_reports: list[RecentReportSummary] = Field(default_factory=list)
    recent_activity: list[AuditLogSummary] = Field(default_factory=list)
    storage: UsagePlaceholder = Field(
        default_factory=lambda: UsagePlaceholder(label="Storage", value="—", available=False)
    )
    api_usage: UsagePlaceholder = Field(
        default_factory=lambda: UsagePlaceholder(label="API Usage", value="—", available=False)
    )
    subscription: UsagePlaceholder = Field(
        default_factory=lambda: UsagePlaceholder(
            label="Subscription",
            value="Coming soon",
            available=False,
        )
    )
