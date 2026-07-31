import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.api.v1.assets import router as assets_router
from app.api.v1.findings import router as findings_router
from app.api.v1.reports import router as reports_router
from app.api.v1.scans import router as scans_router
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.projects.schemas import CreateProjectRequest, UpdateProjectRequest
from app.projects.services import project_service

router = APIRouter()

router.include_router(assets_router, prefix="/{project_id}/assets", tags=["assets"])
router.include_router(scans_router, prefix="/{project_id}/scans", tags=["scans"])
router.include_router(findings_router, prefix="/{project_id}/findings", tags=["findings"])
router.include_router(reports_router, prefix="/{project_id}/reports", tags=["reports"])


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    projects = project_service.list_organization_projects(db, membership)
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


@router.delete("/{project_id}", status_code=200)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_DELETE)),
) -> JSONResponse:
    project_service.delete_organization_project(db, membership, project_id=project_id)
    return success_response(data={"message": "Project deleted successfully"})
