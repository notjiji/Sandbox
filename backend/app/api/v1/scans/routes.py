import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.scans.schemas import CreateScanRequest
from app.scans.services import scan_service

router = APIRouter()


@router.get("")
def list_scans(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_READ)),
) -> JSONResponse:
    result = scan_service.list_project_scans(db, membership, project_id=project_id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_scan(
    project_id: uuid.UUID,
    body: CreateScanRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_CREATE)),
) -> JSONResponse:
    scan = scan_service.create_project_scan(db, membership, project_id=project_id, body=body)
    return success_response(data=scan.model_dump(mode="json"), status_code=201)


@router.get("/{scan_id}")
def get_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_READ)),
) -> JSONResponse:
    scan = scan_service.get_project_scan(db, membership, project_id=project_id, scan_id=scan_id)
    return success_response(data=scan.model_dump(mode="json"))


@router.post("/{scan_id}/run")
def run_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_RUN)),
) -> JSONResponse:
    scan = scan_service.run_project_scan(db, membership, project_id=project_id, scan_id=scan_id)
    return success_response(data=scan.model_dump(mode="json"))


@router.post("/{scan_id}/cancel")
def cancel_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_CANCEL)),
) -> JSONResponse:
    scan = scan_service.cancel_project_scan(db, membership, project_id=project_id, scan_id=scan_id)
    return success_response(data=scan.model_dump(mode="json"))
