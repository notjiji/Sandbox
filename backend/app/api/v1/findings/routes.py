import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.findings.schemas import UpdateFindingRequest
from app.findings.services import finding_service
from app.members.models import OrganizationMember

router = APIRouter()


@router.get("")
def list_findings(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    result = finding_service.list_project_findings(db, membership, project_id=project_id)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{finding_id}")
def get_finding(
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    finding = finding_service.get_project_finding(
        db, membership, project_id=project_id, finding_id=finding_id
    )
    return success_response(data=finding.model_dump(mode="json"))


@router.patch("/{finding_id}")
def update_finding(
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: UpdateFindingRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_UPDATE)),
) -> JSONResponse:
    finding = finding_service.update_project_finding(
        db,
        membership,
        project_id=project_id,
        finding_id=finding_id,
        body=body,
    )
    return success_response(data=finding.model_dump(mode="json"))
