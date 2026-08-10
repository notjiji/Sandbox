import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.reports.enums import ReportStatus, ReportType
from app.reports.schemas import ReportListQuery
from app.reports.services import report_service

router = APIRouter()


@router.get("")
def list_organization_reports(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    report_type: ReportType | None = None,
    status: ReportStatus | None = None,
    search: str | None = None,
    project_id: str | None = None,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> JSONResponse:
    result = report_service.list_organization_reports(
        db,
        membership,
        query=ReportListQuery(
            page=page,
            limit=limit,
            report_type=report_type,
            status=status,
            search=search,
            project_id=project_id,
        ),
    )
    return success_response(data=result.model_dump(mode="json"))
