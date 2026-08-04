import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.assets.enums import (
    AssetCriticality,
    AssetEnvironment,
    AssetStatus,
    AssetType,
)
from app.assets.models import Asset, AssetMetadataEntry, AssetTag


def _asset_query(db: Session, *, include_deleted: bool = False):
    query = db.query(Asset).options(
        joinedload(Asset.metadata_entries),
        joinedload(Asset.tags),
        joinedload(Asset.parent),
    )
    if not include_deleted:
        query = query.filter(Asset.deleted_at.is_(None))
    return query


def _apply_list_filters(
    query,
    *,
    status: AssetStatus | None = None,
    asset_type: AssetType | None = None,
    criticality: AssetCriticality | None = None,
    environment: AssetEnvironment | None = None,
    search: str | None = None,
):
    if status == AssetStatus.DELETED:
        query = query.filter(Asset.deleted_at.isnot(None))
    else:
        query = query.filter(Asset.deleted_at.is_(None))
        if status is not None:
            query = query.filter(Asset.status == status)

    if asset_type is not None:
        query = query.filter(Asset.type == asset_type)
    if criticality is not None:
        query = query.filter(Asset.criticality == criticality)
    if environment is not None:
        query = query.filter(Asset.environment == environment)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = (
            query.outerjoin(AssetTag)
            .outerjoin(AssetMetadataEntry)
            .filter(
                or_(
                    Asset.name.ilike(term),
                    Asset.description.ilike(term),
                    Asset.owner.ilike(term),
                    AssetTag.tag.ilike(term),
                    AssetMetadataEntry.value.ilike(term),
                )
            )
            .distinct()
        )
    return query


def list_assets_for_project(
    db: Session,
    *,
    project_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    status: AssetStatus | None = None,
    asset_type: AssetType | None = None,
    criticality: AssetCriticality | None = None,
    environment: AssetEnvironment | None = None,
    search: str | None = None,
    roots_only: bool = False,
    parent_id: uuid.UUID | None = None,
) -> tuple[list[Asset], int]:
    query = db.query(Asset).filter(Asset.project_id == project_id)
    if parent_id is not None:
        query = query.filter(Asset.parent_id == parent_id)
    elif roots_only:
        query = query.filter(Asset.parent_id.is_(None))

    query = _apply_list_filters(
        query,
        status=status,
        asset_type=asset_type,
        criticality=criticality,
        environment=environment,
        search=search,
    )

    total = query.with_entities(func.count(func.distinct(Asset.id))).scalar() or 0
    offset = (page - 1) * limit
    if parent_id is not None or roots_only:
        order_by = (Asset.created_at.asc(),)
    else:
        order_by = (
            func.coalesce(Asset.parent_id, Asset.id),
            Asset.parent_id.asc().nullsfirst(),
            Asset.created_at.asc(),
        )
    asset_ids = [
        row[0]
        for row in (
            query.with_entities(Asset.id)
            .distinct()
            .order_by(*order_by)
            .offset(offset)
            .limit(limit)
            .all()
        )
    ]
    if not asset_ids:
        return [], total

    assets = (
        _asset_query(db, include_deleted=status == AssetStatus.DELETED)
        .filter(Asset.id.in_(asset_ids))
        .all()
    )
    order = {asset_id: index for index, asset_id in enumerate(asset_ids)}
    assets.sort(key=lambda asset: order[asset.id])
    return assets, total


def list_child_assets(
    db: Session,
    *,
    parent_id: uuid.UUID,
    status: AssetStatus | None = None,
    asset_type: AssetType | None = None,
    criticality: AssetCriticality | None = None,
    environment: AssetEnvironment | None = None,
    search: str | None = None,
) -> list[Asset]:
    query = _asset_query(db, include_deleted=status == AssetStatus.DELETED).filter(
        Asset.parent_id == parent_id
    )
    query = _apply_list_filters(
        query,
        status=status,
        asset_type=asset_type,
        criticality=criticality,
        environment=environment,
        search=search,
    )
    return query.order_by(Asset.created_at.asc()).all()


def get_asset_by_id_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset_id: uuid.UUID,
    include_deleted: bool = False,
) -> Asset | None:
    query = _asset_query(db, include_deleted=include_deleted).filter(
        Asset.id == asset_id,
        Asset.organization_id == organization_id,
    )
    return query.first()


def get_asset_by_id(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    include_deleted: bool = False,
) -> Asset | None:
    return (
        _asset_query(db, include_deleted=include_deleted)
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


def archive_asset(db: Session, asset: Asset) -> Asset:
    asset.status = AssetStatus.ARCHIVED
    db.add(asset)
    db.flush()
    return asset


def restore_asset(db: Session, asset: Asset) -> Asset:
    asset.status = AssetStatus.ACTIVE
    asset.deleted_at = None
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
