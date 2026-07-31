import uuid

from sqlalchemy.orm import Session, joinedload

from app.assets.enums import (
    AssetCriticality,
    AssetEnvironment,
    AssetStatus,
    AssetType,
)
from app.assets.models import Asset, AssetMetadataEntry, AssetTag


def _asset_query(db: Session):
    return (
        db.query(Asset)
        .options(
            joinedload(Asset.metadata_entries),
            joinedload(Asset.tags),
        )
        .filter(Asset.deleted_at.is_(None))
    )


def list_assets_for_project(db: Session, *, project_id: uuid.UUID) -> list[Asset]:
    return (
        _asset_query(db)
        .filter(Asset.project_id == project_id)
        .order_by(Asset.parent_id.asc().nullsfirst(), Asset.created_at.asc())
        .all()
    )


def list_child_assets(db: Session, *, parent_id: uuid.UUID) -> list[Asset]:
    return (
        _asset_query(db)
        .filter(Asset.parent_id == parent_id)
        .order_by(Asset.created_at.asc())
        .all()
    )


def get_asset_by_id(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> Asset | None:
    return (
        _asset_query(db)
        .filter(Asset.id == asset_id, Asset.project_id == project_id)
        .first()
    )


def create_asset(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    name: str,
    type: AssetType = AssetType.WEBSITE,
    parent_id: uuid.UUID | None = None,
    description: str | None = None,
    status: AssetStatus = AssetStatus.PENDING,
    environment: AssetEnvironment = AssetEnvironment.PRODUCTION,
    criticality: AssetCriticality = AssetCriticality.MEDIUM,
    owner: str | None = None,
    created_by: uuid.UUID | None = None,
) -> Asset:
    asset = Asset(
        organization_id=organization_id,
        project_id=project_id,
        parent_id=parent_id,
        name=name,
        type=type,
        description=description,
        status=status,
        environment=environment,
        criticality=criticality,
        owner=owner,
        created_by=created_by,
    )
    db.add(asset)
    db.flush()
    return asset


def update_asset(
    db: Session,
    asset: Asset,
    *,
    name: str | None = None,
    description: str | None = None,
    type: AssetType | None = None,
    status: AssetStatus | None = None,
    environment: AssetEnvironment | None = None,
    criticality: AssetCriticality | None = None,
    owner: str | None = None,
    parent_id: uuid.UUID | None = None,
    clear_parent: bool = False,
) -> Asset:
    if name is not None:
        asset.name = name
    if description is not None:
        asset.description = description
    if type is not None:
        asset.type = type
    if status is not None:
        asset.status = status
    if environment is not None:
        asset.environment = environment
    if criticality is not None:
        asset.criticality = criticality
    if owner is not None:
        asset.owner = owner
    if clear_parent:
        asset.parent_id = None
    elif parent_id is not None:
        asset.parent_id = parent_id
    db.add(asset)
    db.flush()
    return asset


def soft_delete_asset(db: Session, asset: Asset) -> None:
    from datetime import datetime, timezone

    asset.status = AssetStatus.DELETED
    asset.deleted_at = datetime.now(timezone.utc)
    db.add(asset)
    db.flush()


def upsert_metadata_entries(
    db: Session,
    *,
    asset_id: uuid.UUID,
    metadata: dict[str, str],
) -> list[AssetMetadataEntry]:
    if not metadata:
        return []

    existing = {
        entry.key: entry
        for entry in db.query(AssetMetadataEntry).filter(AssetMetadataEntry.asset_id == asset_id).all()
    }
    updated: list[AssetMetadataEntry] = []
    for key, value in metadata.items():
        normalized_key = key.strip()
        normalized_value = value.strip()
        if not normalized_key or not normalized_value:
            continue
        entry = existing.get(normalized_key)
        if entry:
            entry.value = normalized_value
        else:
            entry = AssetMetadataEntry(
                asset_id=asset_id,
                key=normalized_key,
                value=normalized_value,
            )
            db.add(entry)
        updated.append(entry)
    db.flush()
    return updated


def replace_tags(db: Session, *, asset_id: uuid.UUID, tags: list[str]) -> list[AssetTag]:
    db.query(AssetTag).filter(AssetTag.asset_id == asset_id).delete()
    normalized = sorted({tag.strip().lower() for tag in tags if tag.strip()})
    created: list[AssetTag] = []
    for tag in normalized:
        entry = AssetTag(asset_id=asset_id, tag=tag)
        db.add(entry)
        created.append(entry)
    db.flush()
    return created
