import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.assets.router import router as assets_router
from app.findings.router import router as findings_router
from app.reports.router import router as reports_router
from app.risk.router import router as risk_router
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.projects.schemas import CreateProjectRequest, UpdateProjectRequest
from app.projects.services import project_service
from app.projects.services.overview_service import get_project_activity, get_project_overview

router = APIRouter()

router.include_router(assets_router, prefix="/{project_id}/assets", tags=["assets"])
router.include_router(findings_router, prefix="/{project_id}/findings", tags=["findings"])
router.include_router(reports_router, prefix="/{project_id}/reports", tags=["reports"])
router.include_router(risk_router, prefix="/{project_id}/risk", tags=["risk"])


@router.get("")
def list_projects(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    projects = project_service.list_organization_projects(
        db, membership, include_inactive=include_inactive
    )
    return success_response(
        data={
            "items": [project.model_dump(mode="json") for project in projects],
            "total": len(projects),
        }
    )


@router.post("", status_code=201)
def create_project(
    body: CreateProjectRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_CREATE)),
) -> JSONResponse:
    project = project_service.create_organization_project(db, membership, body=body)
    return success_response(data=project.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}")
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    project = project_service.get_organization_project(db, membership, project_id=project_id)
    return success_response(data=project.model_dump(mode="json"))


@router.get("/{project_id}/overview")
def get_project_overview_route(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    overview = get_project_overview(db, membership, project_id=project_id)
    return success_response(data=overview.model_dump(mode="json"))


@router.get("/{project_id}/activity")
def get_project_activity_route(
    project_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    activity = get_project_activity(
        db, membership, project_id=project_id, page=page, limit=limit
    )
    return success_response(data=activity.model_dump(mode="json"))


@router.patch("/{project_id}")
def patch_project(
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
) -> JSONResponse:
    project = project_service.update_organization_project(
        db,
        membership,
        project_id=project_id,
        body=body,
    )
    return success_response(data=project.model_dump(mode="json"))


@router.patch("/{project_id}/archive")
def archive_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
) -> JSONResponse:
    project = project_service.archive_organization_project(
        db, membership, project_id=project_id
    )
    return success_response(data=project.model_dump(mode="json"))


@router.patch("/{project_id}/restore")
def restore_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
) -> JSONResponse:
    project = project_service.restore_organization_project(
        db, membership, project_id=project_id
    )
    return success_response(data=project.model_dump(mode="json"))


@router.delete("/{project_id}", status_code=200)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_DELETE)),
) -> JSONResponse:
    project_service.delete_organization_project(db, membership, project_id=project_id)
    return success_response(data={"message": "Project deleted successfully"})
