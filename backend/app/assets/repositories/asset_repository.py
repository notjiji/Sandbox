import uuid

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload

from app.assets.enums import (
    AssetCategory,
    AssetCriticality,
    AssetEnvironment,
    AssetSortField,
    AssetStatus,
    AssetType,
    SortOrder,
)
from app.assets.models import Asset, AssetMetadataEntry, AssetTag
from app.assets.tag_filters import normalize_tags, tag_match_condition


def _asset_query(db: Session, *, include_deleted: bool = False):
    query = db.query(Asset).options(
        joinedload(Asset.metadata_entries),
        joinedload(Asset.tags),
        joinedload(Asset.parent),
        joinedload(Asset.organization),
        joinedload(Asset.project),
        joinedload(Asset.creator),
        joinedload(Asset.updater),
        joinedload(Asset.archiver),
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
    asset_category: AssetCategory | None = None,
    search: str | None = None,
    tags: list[str] | None = None,
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
    if asset_category is not None:
        query = query.filter(Asset.asset_category == asset_category)

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
                    Asset.external_identifier.ilike(term),
                    Asset.business_unit.ilike(term),
                    AssetTag.tag.ilike(term),
                    AssetMetadataEntry.value.ilike(term),
                )
            )
            .distinct()
        )

    for tag in normalize_tags(tags):
        query = query.filter(tag_match_condition(tag))

    return query


def _sort_expression(sort: AssetSortField):
    if sort == AssetSortField.NAME:
        return Asset.name
    if sort == AssetSortField.UPDATED_AT:
        return Asset.updated_at
    if sort == AssetSortField.CRITICALITY:
        return case(
            (Asset.criticality == AssetCriticality.CRITICAL, 4),
            (Asset.criticality == AssetCriticality.HIGH, 3),
            (Asset.criticality == AssetCriticality.MEDIUM, 2),
            (Asset.criticality == AssetCriticality.LOW, 1),
            else_=0,
        )
    if sort == AssetSortField.ENVIRONMENT:
        return Asset.environment
    if sort == AssetSortField.TYPE:
        return Asset.type
    return Asset.created_at


def _resolve_order_by(
    *,
    sort: AssetSortField,
    order: SortOrder,
    roots_only: bool,
    parent_id: uuid.UUID | None,
):
    column = _sort_expression(sort)
    direction = column.desc() if order == SortOrder.DESC else column.asc()
    if parent_id is not None:
        return (direction, Asset.id.asc())
    if roots_only:
        return (direction, Asset.id.asc())
    return (direction, Asset.id.asc())


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
    asset_category: AssetCategory | None = None,
    search: str | None = None,
    tags: list[str] | None = None,
    sort: AssetSortField = AssetSortField.CREATED_AT,
    order: SortOrder = SortOrder.ASC,
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
        asset_category=asset_category,
        search=search,
        tags=tags,
    )

    total = query.with_entities(func.count(func.distinct(Asset.id))).scalar() or 0
    offset = (page - 1) * limit
    order_by = _resolve_order_by(
        sort=sort,
        order=order,
        roots_only=roots_only,
        parent_id=parent_id,
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
    asset_category: AssetCategory | None = None,
    search: str | None = None,
    tags: list[str] | None = None,
    sort: AssetSortField = AssetSortField.CREATED_AT,
    order: SortOrder = SortOrder.ASC,
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
        asset_category=asset_category,
        search=search,
        tags=tags,
    )
    column = _sort_expression(sort)
    direction = column.desc() if order == SortOrder.DESC else column.asc()
    return query.order_by(direction, Asset.id.asc()).all()


def list_project_tag_facets(
    db: Session,
    *,
    project_id: uuid.UUID,
    limit: int = 50,
) -> list[tuple[str, int]]:
    custom_rows = (
        db.query(AssetTag.tag, func.count(func.distinct(AssetTag.asset_id)))
        .join(Asset, Asset.id == AssetTag.asset_id)
        .filter(Asset.project_id == project_id, Asset.deleted_at.is_(None))
        .group_by(AssetTag.tag)
        .all()
    )
    counts: dict[str, int] = {tag: int(count) for tag, count in custom_rows}

    for environment in AssetEnvironment:
        token = environment.value
        count = (
            db.query(func.count(Asset.id))
            .filter(
                Asset.project_id == project_id,
                Asset.deleted_at.is_(None),
                Asset.environment == environment,
            )
            .scalar()
            or 0
        )
        if count:
            counts[token] = counts.get(token, 0) + int(count)

    for criticality in AssetCriticality:
        token = criticality.value
        count = (
            db.query(func.count(Asset.id))
            .filter(
                Asset.project_id == project_id,
                Asset.deleted_at.is_(None),
                Asset.criticality == criticality,
            )
            .scalar()
            or 0
        )
        if count:
            counts[token] = counts.get(token, 0) + int(count)

    for asset_type in (AssetType.WEBSITE, AssetType.SERVER, AssetType.DOCKER_HOST, AssetType.DOMAIN):
        token = asset_type.value
        count = (
            db.query(func.count(Asset.id))
            .filter(
                Asset.project_id == project_id,
                Asset.deleted_at.is_(None),
                Asset.type == asset_type,
            )
            .scalar()
            or 0
        )
        if count:
            counts[token] = counts.get(token, 0) + int(count)

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:limit]


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
    external_identifier: str | None = None,
    business_unit: str | None = None,
    asset_category: AssetCategory | None = None,
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
        external_identifier=external_identifier,
        business_unit=business_unit,
        asset_category=asset_category,
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
    external_identifier: str | None = None,
    business_unit: str | None = None,
    asset_category: AssetCategory | None = None,
    updated_by: uuid.UUID | None = None,
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
    if external_identifier is not None:
        asset.external_identifier = external_identifier or None
    if business_unit is not None:
        asset.business_unit = business_unit or None
    if asset_category is not None:
        asset.asset_category = asset_category
    if updated_by is not None:
        asset.updated_by = updated_by
    if clear_parent:
        asset.parent_id = None
    elif parent_id is not None:
        asset.parent_id = parent_id
    db.add(asset)
    db.flush()
    return asset


def archive_asset(
    db: Session,
    asset: Asset,
    *,
    archived_by: uuid.UUID | None = None,
) -> Asset:
    from datetime import datetime, timezone

    asset.status = AssetStatus.ARCHIVED
    asset.archived_at = datetime.now(timezone.utc)
    asset.archived_by = archived_by
    db.add(asset)
    db.flush()
    return asset


def restore_asset(db: Session, asset: Asset) -> Asset:
    asset.status = AssetStatus.ACTIVE
    asset.deleted_at = None
    asset.archived_at = None
    asset.archived_by = None
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
