import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.reports.schemas import CreateReportRequest, ReportListQuery, UpdateReportRequest
from app.reports.services import report_service

router = APIRouter()


@router.get("")
def list_reports(
    project_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    report_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> JSONResponse:
    query = ReportListQuery(page=page, limit=limit, search=search)
    if report_type:
        from app.reports.enums import ReportType

        query.report_type = ReportType(report_type)
    if status:
        from app.reports.enums import ReportStatus

        query.status = ReportStatus(status)
    result = report_service.list_project_reports(
        db, membership, project_id=project_id, query=query
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_report(
    project_id: uuid.UUID,
    body: CreateReportRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    report = report_service.create_project_report(db, membership, project_id=project_id, body=body)
    return success_response(data=report.model_dump(mode="json"), status_code=201)


@router.get("/{report_id}")
def get_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> JSONResponse:
    report = report_service.get_project_report(
        db, membership, project_id=project_id, report_id=report_id
    )
    return success_response(data=report.model_dump(mode="json"))


@router.patch("/{report_id}")
def update_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    body: UpdateReportRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    report = report_service.update_project_report(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
        body=body,
    )
    return success_response(data=report.model_dump(mode="json"))


@router.get("/{report_id}/download")
def download_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> FileResponse:
    report, path = report_service.resolve_report_download(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
    )
    filename = f"{report.name.replace(' ', '-').lower()}.pdf"
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/{report_id}/preview")
def preview_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> HTMLResponse:
    html = report_service.preview_project_report(
        db, membership, project_id=project_id, report_id=report_id
    )
    return HTMLResponse(content=html)


@router.post("/{report_id}/regenerate")
def regenerate_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    report = report_service.regenerate_project_report(
        db, membership, project_id=project_id, report_id=report_id
    )
    return success_response(data=report.model_dump(mode="json"))


@router.post("/{report_id}/generate")
def generate_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    report = report_service.generate_project_report(
        db, membership, project_id=project_id, report_id=report_id
    )
    return success_response(data=report.model_dump(mode="json"))


@router.delete("/{report_id}", status_code=200)
def delete_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_DELETE)),
) -> JSONResponse:
    report_service.delete_project_report(db, membership, project_id=project_id, report_id=report_id)
    return success_response(data={"message": "Report deleted successfully"})
