"""Tag facet queries for asset list filters."""

from __future__ import annotations

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.assets.models import Asset, AssetTag
from app.assets.tag_filters import STRUCTURED_TAG_FIELDS, tag_match_condition


def list_tag_facets_for_project(db: Session, *, project_id: uuid.UUID) -> list[tuple[str, int]]:
    explicit = (
        db.query(AssetTag.tag, func.count(func.distinct(AssetTag.asset_id)))
        .join(Asset, Asset.id == AssetTag.asset_id)
        .filter(Asset.project_id == project_id, Asset.deleted_at.is_(None))
        .group_by(AssetTag.tag)
        .all()
    )
    facets: dict[str, int] = {tag: int(count) for tag, count in explicit}

    base = db.query(Asset).filter(Asset.project_id == project_id, Asset.deleted_at.is_(None))
    for token in STRUCTURED_TAG_FIELDS:
        if token in facets:
            continue
        count = base.filter(tag_match_condition(token)).count()
        if count > 0:
            facets[token] = int(count)

    return sorted(facets.items(), key=lambda item: (-item[1], item[0]))
