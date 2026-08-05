"""Tag filter resolution — maps tag tokens to asset tags or structured fields."""

from __future__ import annotations

from sqlalchemy import and_, exists, or_

from app.assets.enums import (
    AssetCategory,
    AssetCriticality,
    AssetEnvironment,
    AssetType,
)
from app.assets.models import Asset, AssetTag

STRUCTURED_TAG_FIELDS: dict[str, tuple[str, object]] = {
    "production": ("environment", AssetEnvironment.PRODUCTION),
    "staging": ("environment", AssetEnvironment.STAGING),
    "development": ("environment", AssetEnvironment.DEVELOPMENT),
    "testing": ("environment", AssetEnvironment.TESTING),
    "critical": ("criticality", AssetCriticality.CRITICAL),
    "high": ("criticality", AssetCriticality.HIGH),
    "medium": ("criticality", AssetCriticality.MEDIUM),
    "low": ("criticality", AssetCriticality.LOW),
    "website": ("type", AssetType.WEBSITE),
    "domain": ("type", AssetType.DOMAIN),
    "server": ("type", AssetType.SERVER),
    "docker": ("type", AssetType.DOCKER_HOST),
    "docker_host": ("type", AssetType.DOCKER_HOST),
    "kubernetes": ("type", AssetType.KUBERNETES_CLUSTER),
    "api": ("type", AssetType.API_ENDPOINT),
    "cloud": ("type", AssetType.CLOUD_ACCOUNT),
    "infrastructure": ("asset_category", AssetCategory.INFRASTRUCTURE),
    "application": ("asset_category", AssetCategory.APPLICATION),
    "network": ("asset_category", AssetCategory.NETWORK),
    "identity": ("asset_category", AssetCategory.IDENTITY),
    "endpoint": ("asset_category", AssetCategory.ENDPOINT),
}


def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        token = tag.strip().lower()
        if not token or token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


def tag_match_condition(tag: str):
    structured = STRUCTURED_TAG_FIELDS.get(tag)
    tag_exists = exists().where(
        and_(AssetTag.asset_id == Asset.id, AssetTag.tag == tag)
    )
    if structured is None:
        return tag_exists
    field_name, enum_value = structured
    column = getattr(Asset, field_name)
    return or_(column == enum_value, tag_exists)
