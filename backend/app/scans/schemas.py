from datetime import datetime

from pydantic import Field

from app.scans.enums import ScanStatus, ScanType
from app.schemas.base import BaseSchema


class ScanSummary(BaseSchema):
    id: str
    project_id: str
    asset_id: str
    status: ScanStatus
    scan_type: ScanType
    created_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ScanListResponse(BaseSchema):
    items: list[ScanSummary]
    total: int


class CreateScanRequest(BaseSchema):
    asset_id: str = Field(min_length=1)
    scan_type: ScanType = ScanType.FULL
