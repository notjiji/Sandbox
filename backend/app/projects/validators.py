import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.projects.models import Project
from app.projects.repositories.project_repository import get_project_by_id


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


def require_org_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
):
    require_active_project(db, membership, project_id)
    from app.assets.repositories.asset_repository import get_asset_by_id_for_organization

    asset = get_asset_by_id_for_organization(
        db,
        organization_id=membership.organization_id,
        asset_id=asset_id,
    )
    if asset is None or asset.project_id != project_id:
        raise NotFoundError("Asset")
    return asset
