import uuid

from sqlalchemy.orm import Session

from app.assets.enums import AssetStatus, AssetType
from app.assets.models import Asset


def list_assets_for_project(db: Session, *, project_id: uuid.UUID) -> list[Asset]:
    return (
        db.query(Asset)
        .filter(Asset.project_id == project_id)
        .order_by(Asset.parent_id.asc().nullsfirst(), Asset.created_at.asc())
        .all()
    )


def list_child_assets(db: Session, *, parent_id: uuid.UUID) -> list[Asset]:
    return (
        db.query(Asset)
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
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.project_id == project_id)
        .first()
    )


def create_asset(
    db: Session,
    *,
    project_id: uuid.UUID,
    name: str,
    identifier: str | None = None,
    type: AssetType = AssetType.WEBSITE,
    parent_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
) -> Asset:
    asset = Asset(
        project_id=project_id,
        parent_id=parent_id,
        name=name,
        identifier=identifier,
        type=type,
        status=AssetStatus.ACTIVE,
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
    identifier: str | None = None,
    type: AssetType | None = None,
    status: AssetStatus | None = None,
    parent_id: uuid.UUID | None = None,
    clear_parent: bool = False,
) -> Asset:
    if name is not None:
        asset.name = name
    if identifier is not None:
        asset.identifier = identifier
    if type is not None:
        asset.type = type
    if status is not None:
        asset.status = status
    if clear_parent:
        asset.parent_id = None
    elif parent_id is not None:
        asset.parent_id = parent_id
    db.add(asset)
    db.flush()
    return asset


def delete_asset(db: Session, asset: Asset) -> None:
    db.delete(asset)
