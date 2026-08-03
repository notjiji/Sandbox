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
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ScanSummary(BaseSchema):
    id: str
    project_id: str
    asset_id: str
    status: ScanStatus
    scan_type: ScanType
    created_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    plugin_runs: list[ScanPluginRunSummary] = Field(default_factory=list)


class ScanListResponse(BaseSchema):
    items: list[ScanSummary]
    total: int


class CreateAssetScanRequest(BaseSchema):
    scan_type: ScanType = ScanType.FULL


class CreateScanRequest(BaseSchema):
    asset_id: str = Field(min_length=1)
    scan_type: ScanType = ScanType.FULL
