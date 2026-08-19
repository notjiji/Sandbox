from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.dashboard.service import (
    get_dashboard_activity,
    get_dashboard_finding_trend,
    get_dashboard_findings_summary,
    get_dashboard_overview,
    get_dashboard_risk_trend,
    get_dashboard_scan_history,
    get_dashboard_top_assets,
    get_dashboard_upcoming_scans,
)
from app.members.models import OrganizationMember

router = APIRouter()


@router.get("/overview")
def dashboard_overview(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    data = get_dashboard_overview(db, membership)
    return success_response(data=data.model_dump(mode="json"))


@router.get("/risk-trend")
def dashboard_risk_trend(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    data = get_dashboard_risk_trend(db, membership)
    return success_response(data=data.model_dump(mode="json"))


@router.get("/findings-summary")
def dashboard_findings_summary(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    data = get_dashboard_findings_summary(db, membership, limit=limit)
    return success_response(data=data.model_dump(mode="json"))


@router.get("/top-assets")
def dashboard_top_assets(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    data = get_dashboard_top_assets(db, membership, limit=limit)
    return success_response(data=data.model_dump(mode="json"))


@router.get("/activity")
def dashboard_activity(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    data = get_dashboard_activity(db, membership, limit=limit)
    return success_response(data=data.model_dump(mode="json"))


@router.get("/upcoming-scans")
def dashboard_upcoming_scans(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    data = get_dashboard_upcoming_scans(db, membership, limit=limit)
    return success_response(data=data.model_dump(mode="json"))


@router.get("/scan-history")
def dashboard_scan_history(
    range_days: int = Query(default=30, ge=7, le=365),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    if range_days not in {7, 30, 90, 365}:
        range_days = 30
    data = get_dashboard_scan_history(
        db,
        membership,
        range_days=range_days,
        limit=limit,
    )
    return success_response(data=data.model_dump(mode="json"))


@router.get("/finding-trend")
def dashboard_finding_trend(
    range_days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.DASHBOARD_VIEW)),
) -> JSONResponse:
    if range_days not in {7, 30, 90, 365}:
        range_days = 30
    data = get_dashboard_finding_trend(
        db,
        membership,
        range_days=range_days,
    )
    return success_response(data=data.model_dump(mode="json"))
