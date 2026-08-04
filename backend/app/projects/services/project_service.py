import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.slug import slugify, unique_slug
from app.members.models import OrganizationMember
from app.projects.events import ProjectAuditAction
from app.projects.models import Project
from app.projects.repositories.project_repository import (
    create_project,
    deactivate_project,
    get_project_by_id,
    get_project_by_slug,
    list_projects_for_organization,
    update_project,
)
from app.projects.schemas import CreateProjectRequest, ProjectSummary, UpdateProjectRequest
from app.audit.service import record_audit_event


def to_project_summary(project: Project) -> ProjectSummary:
    return ProjectSummary(
        id=str(project.id),
        organization_id=str(project.organization_id),
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_by=str(project.created_by) if project.created_by else None,
        is_active=project.is_active,
    )


def _resolve_project_slug(
    db: Session,
    *,
    organization_id: uuid.UUID,
    name: str,
    slug: str | None,
) -> str:
    candidate = slugify(slug or name)
    if not get_project_by_slug(db, organization_id=organization_id, slug=candidate):
        return candidate
    return unique_slug(name, suffix=uuid.uuid4())


def list_organization_projects(
    db: Session,
    membership: OrganizationMember,
    *,
    include_inactive: bool = False,
) -> list[ProjectSummary]:
    projects = list_projects_for_organization(
        db,
        organization_id=membership.organization_id,
        include_inactive=include_inactive,
    )
    return [to_project_summary(project) for project in projects]


def get_organization_project(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    require_active: bool = False,
) -> ProjectSummary:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project or (require_active and not project.is_active):
        raise NotFoundError("Project")
    return to_project_summary(project)


def create_organization_project(
    db: Session,
    membership: OrganizationMember,
    *,
    body: CreateProjectRequest,
) -> ProjectSummary:
    organization_id = membership.organization_id
    slug = _resolve_project_slug(
        db,
        organization_id=organization_id,
        name=body.name,
        slug=body.slug,
    )
    project = create_project(
        db,
        organization_id=organization_id,
        name=body.name,
        slug=slug,
        description=body.description,
        created_by=membership.user_id,
    )
    record_audit_event(
        db,
        action=ProjectAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=organization_id,
        resource_type="project",
        resource_id=project.id,
        details={"name": project.name, "slug": project.slug},
    )
    db.commit()
    db.refresh(project)
    return to_project_summary(project)


def update_organization_project(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
) -> ProjectSummary:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project:
        raise NotFoundError("Project")
    if body.is_active is not None:
        raise ValidationAppError("Use archive or restore endpoints to change project status")
    if body.name is None and body.description is None:
        raise ValidationAppError("At least one field must be provided")

    update_project(
        db,
        project,
        name=body.name,
        description=body.description,
    )
    record_audit_event(
        db,
        action=ProjectAuditAction.UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="project",
        resource_id=project.id,
        details=body.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(project)
    return to_project_summary(project)


def archive_organization_project(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> ProjectSummary:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project:
        raise NotFoundError("Project")
    if not project.is_active:
        raise ValidationAppError("Project is already archived")

    update_project(db, project, is_active=False)
    record_audit_event(
        db,
        action=ProjectAuditAction.ARCHIVE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="project",
        resource_id=project.id,
    )
    db.commit()
    db.refresh(project)
    return to_project_summary(project)


def restore_organization_project(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> ProjectSummary:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project:
        raise NotFoundError("Project")
    if project.is_active:
        raise ValidationAppError("Project is already active")

    update_project(db, project, is_active=True)
    record_audit_event(
        db,
        action=ProjectAuditAction.RESTORE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="project",
        resource_id=project.id,
    )
    db.commit()
    db.refresh(project)
    return to_project_summary(project)


def delete_organization_project(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> None:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project:
        raise NotFoundError("Project")

    deactivate_project(db, project)
    record_audit_event(
        db,
        action=ProjectAuditAction.DELETE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="project",
        resource_id=project.id,
    )
    db.commit()
