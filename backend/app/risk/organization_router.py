import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.risk.repositories.risk_repository import get_latest_asset_risk
from app.risk.schemas import AssetRiskResponse, unscanned_asset_risk
from app.risk.service import risk_service

router = APIRouter()


@router.get("")
def get_organization_risk(
    refresh: bool = False,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    result = risk_service.calculate_organization_risk(db, membership, refresh=refresh)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/dashboard")
def get_organization_dashboard(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    result = risk_service.get_dashboard_metrics(db, membership)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/assets/{asset_id}")
def get_asset_risk(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    latest = get_latest_asset_risk(db, asset_id=asset_id)
    if not latest:
        return success_response(data=unscanned_asset_risk(asset_id=str(asset_id)).model_dump(mode="json"))
    result = AssetRiskResponse(
        asset_id=str(latest.asset_id),
        scanned=True,
        scan_id=str(latest.scan_id) if latest.scan_id else None,
        total_risk=float(latest.total_risk),
        score=float(latest.score),
        grade=latest.grade,
        critical_count=latest.critical_count,
        high_count=latest.high_count,
        medium_count=latest.medium_count,
        low_count=latest.low_count,
        calculated_at=latest.calculated_at,
    )
    return success_response(data=result.model_dump(mode="json"))
