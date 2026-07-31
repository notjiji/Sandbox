import uuid

from sqlalchemy.orm import Session

from app.projects.models import Project


def list_projects_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
    include_inactive: bool = False,
) -> list[Project]:
    query = db.query(Project).filter(Project.organization_id == organization_id)
    if not include_inactive:
        query = query.filter(Project.is_active.is_(True))
    return query.order_by(Project.created_at.asc()).all()


def get_project_by_id(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Project | None:
    return (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
        .first()
    )


def get_project_by_slug(
    db: Session,
    *,
    organization_id: uuid.UUID,
    slug: str,
) -> Project | None:
    return (
        db.query(Project)
        .filter(
            Project.organization_id == organization_id,
            Project.slug == slug,
        )
        .first()
    )


def create_project(
    db: Session,
    *,
    organization_id: uuid.UUID,
    name: str,
    slug: str,
    description: str | None = None,
    created_by: uuid.UUID | None = None,
) -> Project:
    project = Project(
        organization_id=organization_id,
        name=name,
        slug=slug,
        description=description,
        created_by=created_by,
        is_active=True,
    )
    db.add(project)
    db.flush()
    return project


def update_project(
    db: Session,
    project: Project,
    *,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> Project:
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if is_active is not None:
        project.is_active = is_active
    db.add(project)
    db.flush()
    return project


def deactivate_project(db: Session, project: Project) -> None:
    project.is_active = False
    db.add(project)
