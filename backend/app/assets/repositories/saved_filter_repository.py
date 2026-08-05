"""Asset saved filter repository."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.saved_filter_models import AssetSavedFilter


def list_saved_filters_for_user(
    db: Session,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[AssetSavedFilter]:
    return (
        db.query(AssetSavedFilter)
        .filter(
            AssetSavedFilter.project_id == project_id,
            AssetSavedFilter.user_id == user_id,
        )
        .order_by(AssetSavedFilter.name.asc())
        .all()
    )


def get_saved_filter(
    db: Session,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    filter_id: uuid.UUID,
) -> AssetSavedFilter | None:
    return (
        db.query(AssetSavedFilter)
        .filter(
            AssetSavedFilter.id == filter_id,
            AssetSavedFilter.project_id == project_id,
            AssetSavedFilter.user_id == user_id,
        )
        .first()
    )


def create_saved_filter(db: Session, saved_filter: AssetSavedFilter) -> AssetSavedFilter:
    db.add(saved_filter)
    db.flush()
    return saved_filter


def delete_saved_filter(db: Session, saved_filter: AssetSavedFilter) -> None:
    db.delete(saved_filter)
    db.flush()
