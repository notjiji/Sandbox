from datetime import datetime

from pydantic import Field

from app.scans.enums import PluginRunStatus, ScanStatus, ScanType
from app.schemas.base import BaseSchema


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


class ScanSummary(BaseSchema):
    id: str
    project_id: str
    asset_id: str
    status: ScanStatus
    scan_type: ScanType
    selected_plugins: list[str] = Field(default_factory=list)
    profile_plugins: list[str] = Field(default_factory=list)
    created_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    plugin_runs: list[ScanPluginRunSummary] = Field(default_factory=list)


class ScanListResponse(BaseSchema):
    items: list[ScanSummary]
    total: int


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
