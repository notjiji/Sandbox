import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.projects.models import Project
from app.projects.repository import get_project_by_id


def require_active_project(
    db: Session,
    membership: OrganizationMember,
    project_id: uuid.UUID,
) -> Project:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project or not project.is_active:
        raise NotFoundError("Project")
    return project
