from datetime import datetime

from pydantic import Field

from app.audit.schemas import AuditLogSummary
from app.organizations.schemas_overview import RecentReportSummary, RecentScanSummary, UsagePlaceholder
from app.projects.schemas import ProjectSummary
from app.risk.schemas import ProjectRiskResponse
from app.shared.schemas.base import BaseSchema


class ProjectStats(BaseSchema):
    assets: int = 0
    scans: int = 0
    open_findings: int = 0
    total_findings: int = 0
    reports: int = 0


class ProjectOverview(BaseSchema):
    project: ProjectSummary
    stats: ProjectStats
    security: ProjectRiskResponse
    recent_scans: list[RecentScanSummary] = Field(default_factory=list)
    recent_reports: list[RecentReportSummary] = Field(default_factory=list)
    recent_activity: list[AuditLogSummary] = Field(default_factory=list)
    ai_summary: UsagePlaceholder = Field(
        default_factory=lambda: UsagePlaceholder(
            label="AI Summary",
            value="Coming soon",
            available=False,
        )
    )


class ProjectActivityResponse(BaseSchema):
    items: list[AuditLogSummary]
    total: int
    page: int
    limit: int
