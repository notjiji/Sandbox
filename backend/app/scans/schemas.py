from datetime import datetime

from pydantic import Field

from app.scans.enums import PluginRunStatus, ScanStatus, ScanType
from app.shared.schemas.base import BaseSchema


class ScanListQuery(BaseSchema):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status: ScanStatus | None = None
    scan_type: ScanType | None = None
    search: str | None = Field(default=None, max_length=255)


class ScanMetrics(BaseSchema):
    duration_seconds: float | None = None
    risk_score: float | None = None
    grade: str | None = None
    critical_count: int = 0
    findings_count: int = 0


class ScanPluginRunSummary(BaseSchema):
    id: str
    asset_id: str
    plugin_name: str
    status: PluginRunStatus
    error_message: str | None = None
    findings_count: int = 0
    duration_seconds: float | None = None
    metadata: dict = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ScanLifecycleTimestamps(BaseSchema):
    pending_at: datetime | None = None
    queued_at: datetime | None = None
    running_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    cancelled_at: datetime | None = None


class ScanSummary(BaseSchema):
    id: str
    project_id: str
    asset_id: str
    status: ScanStatus
    scan_type: ScanType
    selected_plugins: list[str] = Field(default_factory=list)
    profile_plugins: list[str] = Field(default_factory=list)
    created_by: str | None = None
    created_at: datetime | None = None
    lifecycle: ScanLifecycleTimestamps = Field(default_factory=ScanLifecycleTimestamps)
    plugin_runs: list[ScanPluginRunSummary] = Field(default_factory=list)
    metrics: ScanMetrics = Field(default_factory=ScanMetrics)


class ScanListResponse(BaseSchema):
    items: list[ScanSummary]
    total: int
    page: int = 1
    limit: int = 20


class ScanCompareDiff(BaseSchema):
    risk_score_delta: float | None = None
    critical_count_delta: int = 0
    findings_count_delta: int = 0
    duration_seconds_delta: float | None = None


class ScanCompareResponse(BaseSchema):
    scan_a: ScanSummary
    scan_b: ScanSummary
    diff: ScanCompareDiff


class ScanExportFindingSummary(BaseSchema):
    id: str
    title: str
    severity: str
    status: str
    risk_score: float
    plugin: str | None = None


class ScanExportResponse(BaseSchema):
    scan: ScanSummary
    findings: list[ScanExportFindingSummary] = Field(default_factory=list)
    exported_at: datetime


class CreateAssetScanRequest(BaseSchema):
    scan_type: ScanType = ScanType.FULL
    plugins: list[str] | None = Field(
        default=None,
        description="Required when scan_type is custom — plugin slugs to run",
    )


class ScanProfileSummary(BaseSchema):
    profile: ScanType
    label: str
    description: str
    plugins: list[str]


class ScanProfileListResponse(BaseSchema):
    items: list[ScanProfileSummary]


class CreateScanRequest(BaseSchema):
    asset_id: str = Field(min_length=1)
    scan_type: ScanType = ScanType.FULL
