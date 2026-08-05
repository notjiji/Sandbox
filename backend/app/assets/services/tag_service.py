"""Asset tag facet service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.repositories.tag_repository import list_tag_facets_for_project
from app.assets.schemas import AssetTagFacet, AssetTagListResponse
from app.assets.validators import require_active_project
from app.members.models import OrganizationMember


def list_project_tag_facets(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> AssetTagListResponse:
    require_active_project(db, membership, project_id)
    facets = list_tag_facets_for_project(db, project_id=project_id)
    return AssetTagListResponse(
        items=[AssetTagFacet(tag=tag, count=count) for tag, count in facets]
    )
