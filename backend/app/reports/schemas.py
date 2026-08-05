from datetime import datetime

from pydantic import Field

from app.reports.enums import ReportStatus, ReportType
from app.shared.schemas.base import BaseSchema


class ReportSummary(BaseSchema):
    id: str
    project_id: str
    asset_id: str | None = None
    report_type: ReportType
    name: str
    description: str | None = None
    status: ReportStatus
    file_url: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReportListResponse(BaseSchema):
    items: list[ReportSummary]
    total: int
    page: int = 1
    limit: int = 20


class ReportListQuery(BaseSchema):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    report_type: ReportType | None = None
    status: ReportStatus | None = None
    search: str | None = Field(default=None, max_length=255)


class CreateReportRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    report_type: ReportType = ReportType.EXECUTIVE


class CreateAssetReportRequest(BaseSchema):
    report_type: ReportType = ReportType.EXECUTIVE
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    generate: bool = Field(
        default=True,
        description="When true, generate the report immediately after creation",
    )


class UpdateReportRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
