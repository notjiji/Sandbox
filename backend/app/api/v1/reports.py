import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.models.organization_member import OrganizationMember
from app.schemas.report import CreateReportRequest, UpdateReportRequest
from app.services import report as report_service

router = APIRouter()


@router.get("")
def list_reports(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_READ)),
) -> JSONResponse:
    result = report_service.list_project_reports(
        db, membership, project_id=project_id
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_report(
    project_id: uuid.UUID,
    body: CreateReportRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.REPORT_GENERATE)),
) -> JSONResponse:
    report = report_service.create_project_report(
        db, membership, project_id=project_id, body=body
    )
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
    report_service.delete_project_report(
        db, membership, project_id=project_id, report_id=report_id
    )
    return success_response(data={"message": "Report deleted successfully"})
