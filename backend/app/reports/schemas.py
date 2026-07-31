from pydantic import Field

from app.reports.enums import ReportStatus
from app.schemas.base import BaseSchema


class ReportSummary(BaseSchema):
    id: str
    project_id: str
    name: str
    description: str | None = None
    status: ReportStatus
    file_url: str | None = None
    created_by: str | None = None


class ReportListResponse(BaseSchema):
    items: list[ReportSummary]
    total: int


class CreateReportRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)


class UpdateReportRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
