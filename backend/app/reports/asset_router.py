import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.reports.enums import ReportStatus, ReportType
from app.reports.schemas import CreateAssetReportRequest, ReportListQuery
from app.reports.responses import pdf_download_response
from app.reports.services import report_service

router = APIRouter()


@router.get("")
def list_asset_reports(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    report_type: ReportType | None = None,
    status: ReportStatus | None = None,
    search: str | None = Query(None, max_length=255),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> JSONResponse:
    result = report_service.list_asset_reports(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        query=ReportListQuery(
            page=page,
            limit=limit,
            report_type=report_type,
            status=status,
            search=search,
        ),
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_asset_report(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: CreateAssetReportRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    report = report_service.create_asset_report(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        body=body,
    )
    return success_response(data=report.model_dump(mode="json"), status_code=201)


@router.get("/{report_id}/download")
def download_asset_report(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> StreamingResponse:
    report, pdf_bytes = report_service.resolve_report_download(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
        asset_id=asset_id,
    )
    return pdf_download_response(report, pdf_bytes)


@router.get("/{report_id}/preview")
def preview_asset_report(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> HTMLResponse:
    html = report_service.preview_project_report(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
        asset_id=asset_id,
    )
    return HTMLResponse(content=html)


@router.post("/{report_id}/regenerate")
def regenerate_asset_report(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    _ = asset_id
    report = report_service.regenerate_project_report(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
    )
    return success_response(data=report.model_dump(mode="json"))


@router.post("/{report_id}/generate")
def generate_asset_report(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    _ = asset_id
    report = report_service.generate_project_report(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
    )
    return success_response(data=report.model_dump(mode="json"))


@router.get("/{report_id}")
def get_asset_report(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> JSONResponse:
    _ = asset_id
    report = report_service.get_project_report(
        db,
        membership,
        project_id=project_id,
        report_id=report_id,
    )
    return success_response(data=report.model_dump(mode="json"))
