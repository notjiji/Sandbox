import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.scans.enums import SchedulePreset
from app.scans.schemas import UpdateScanScheduleRequest
from app.scans.services import schedule_service

router = APIRouter()


@router.get("")
def list_asset_scan_schedules(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_READ)),
) -> JSONResponse:
    result = schedule_service.list_asset_scan_schedules(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.patch("/{preset}")
def update_asset_scan_schedule(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    preset: SchedulePreset,
    body: UpdateScanScheduleRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.SCAN_CREATE)),
) -> JSONResponse:
    result = schedule_service.update_asset_scan_schedule(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        preset=preset,
        body=body,
    )
    return success_response(data=result.model_dump(mode="json"))
