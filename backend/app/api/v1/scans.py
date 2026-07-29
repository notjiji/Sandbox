import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import require_permission
from app.core.permissions import Permission
from app.core.responses import success_response
from app.models.organization_member import OrganizationMember
from app.schemas.scan import CreateScanRequest
from app.services import scan as scan_service

router = APIRouter()


@router.get("")
def list_scans(
    _membership: OrganizationMember = Depends(require_permission(Permission.SCAN_READ)),
) -> JSONResponse:
    result = scan_service.list_scans()
    return success_response(data=result.model_dump(mode="json"))


@router.post("", status_code=201)
def create_scan(
    body: CreateScanRequest,
    _membership: OrganizationMember = Depends(require_permission(Permission.SCAN_CREATE)),
) -> JSONResponse:
    scan_service.create_scan(body=body)
    return success_response(data={})


@router.get("/{scan_id}")
def get_scan(
    scan_id: uuid.UUID,
    _membership: OrganizationMember = Depends(require_permission(Permission.SCAN_READ)),
) -> JSONResponse:
    scan_service.get_scan(scan_id=str(scan_id))
    return success_response(data={})


@router.post("/{scan_id}/run")
def run_scan(
    scan_id: uuid.UUID,
    _membership: OrganizationMember = Depends(require_permission(Permission.SCAN_RUN)),
) -> JSONResponse:
    scan_service.run_scan(scan_id=str(scan_id))
    return success_response(data={})


@router.post("/{scan_id}/cancel")
def cancel_scan(
    scan_id: uuid.UUID,
    _membership: OrganizationMember = Depends(require_permission(Permission.SCAN_CANCEL)),
) -> JSONResponse:
    scan_service.cancel_scan(scan_id=str(scan_id))
    return success_response(data={})
