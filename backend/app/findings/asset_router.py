import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.schemas import FindingListQuery, UpdateFindingRequest
from app.findings.services import finding_service
from app.members.models import OrganizationMember

router = APIRouter()


@router.get("")
def list_asset_findings(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_group: str | None = Query(None, pattern="^(open|resolved|ignored)$"),
    status: FindingStatus | None = None,
    severity: FindingSeverity | None = None,
    search: str | None = Query(None, max_length=255),
    sort: str = Query("risk_score", pattern="^(risk_score|severity|title|created_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    result = finding_service.list_asset_findings(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        query=FindingListQuery(
            page=page,
            limit=limit,
            status_group=status_group,
            status=status,
            severity=severity,
            search=search,
            sort=sort,
            order=order,
        ),
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{finding_id}")
def get_asset_finding(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    _ = asset_id
    finding = finding_service.get_project_finding(
        db,
        membership,
        project_id=project_id,
        finding_id=finding_id,
    )
    return success_response(data=finding.model_dump(mode="json"))


@router.patch("/{finding_id}")
def update_asset_finding(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: UpdateFindingRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_UPDATE)),
) -> JSONResponse:
    _ = asset_id
    finding = finding_service.update_project_finding(
        db,
        membership,
        project_id=project_id,
        finding_id=finding_id,
        body=body,
    )
    return success_response(data=finding.model_dump(mode="json"))
