"""Saved asset filter presets per user."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.repositories.saved_filter_repository import (
    create_saved_filter,
    delete_saved_filter,
    get_saved_filter,
    list_saved_filters_for_user,
)
from app.assets.saved_filter_models import AssetSavedFilter
from app.assets.schemas import (
    AssetSavedFilterListResponse,
    AssetSavedFilterState,
    AssetSavedFilterSummary,
    CreateAssetSavedFilterRequest,
)
from app.assets.validators import require_active_project
from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember


def _to_summary(saved_filter: AssetSavedFilter) -> AssetSavedFilterSummary:
    filters = AssetSavedFilterState.model_validate(saved_filter.filters_json)
    return AssetSavedFilterSummary(
        id=str(saved_filter.id),
        name=saved_filter.name,
        filters=filters,
        created_at=saved_filter.created_at,
        updated_at=saved_filter.updated_at,
    )


def list_saved_filters(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> AssetSavedFilterListResponse:
    require_active_project(db, membership, project_id)
    items = list_saved_filters_for_user(
        db,
        project_id=project_id,
        user_id=membership.user_id,
    )
    return AssetSavedFilterListResponse(items=[_to_summary(item) for item in items])


def create_saved_filter_for_user(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: CreateAssetSavedFilterRequest,
) -> AssetSavedFilterSummary:
    require_active_project(db, membership, project_id)
    existing = list_saved_filters_for_user(
        db,
        project_id=project_id,
        user_id=membership.user_id,
    )
    if any(item.name.lower() == body.name.strip().lower() for item in existing):
        raise ValidationAppError("A saved filter with this name already exists")

    saved_filter = AssetSavedFilter(
        organization_id=membership.organization_id,
        project_id=project_id,
        user_id=membership.user_id,
        name=body.name.strip(),
        filters_json=body.filters.model_dump(mode="json"),
    )
    create_saved_filter(db, saved_filter)
    db.commit()
    db.refresh(saved_filter)
    return _to_summary(saved_filter)


def delete_saved_filter_for_user(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    filter_id: uuid.UUID,
) -> None:
    require_active_project(db, membership, project_id)
    saved_filter = get_saved_filter(
        db,
        project_id=project_id,
        user_id=membership.user_id,
        filter_id=filter_id,
    )
    if not saved_filter:
        raise NotFoundError("Saved filter")
    delete_saved_filter(db, saved_filter)
    db.commit()
