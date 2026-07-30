import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.models.organization_member import OrganizationMember
from app.schemas.project import CreateProjectRequest, UpdateProjectRequest
from app.services.project import (
    create_organization_project,
    delete_organization_project,
    get_organization_project,
    list_organization_projects,
    update_organization_project,
)

router = APIRouter()


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    projects = list_organization_projects(db, membership)
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
    project = create_organization_project(db, membership, body=body)
    return success_response(data=project.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}")
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_READ)),
) -> JSONResponse:
    project = get_organization_project(db, membership, project_id=project_id)
    return success_response(data=project.model_dump(mode="json"))


@router.patch("/{project_id}")
def patch_project(
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.PROJECT_UPDATE)),
) -> JSONResponse:
    project = update_organization_project(
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
    delete_organization_project(db, membership, project_id=project_id)
    return success_response(data={"message": "Project deleted successfully"})
