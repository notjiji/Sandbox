from pydantic import Field

from app.schemas.base import BaseSchema


class ScanSummary(BaseSchema):
    id: str
    asset_id: str
    status: str
    scan_type: str


class ScanListResponse(BaseSchema):
    items: list[ScanSummary]
    total: int


class CreateScanRequest(BaseSchema):
    asset_id: str = Field(min_length=1)
    scan_type: str = Field(default="full", min_length=1, max_length=64)
