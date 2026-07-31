import uuid

from sqlalchemy.orm import Session

from app.assets.models import Asset, AssetStatus, AssetType


def list_assets_for_project(db: Session, *, project_id: uuid.UUID) -> list[Asset]:
    return (
        db.query(Asset)
        .filter(Asset.project_id == project_id)
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
    type: AssetType = AssetType.HOST,
    created_by: uuid.UUID | None = None,
) -> Asset:
    asset = Asset(
        project_id=project_id,
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
) -> Asset:
    if name is not None:
        asset.name = name
    if identifier is not None:
        asset.identifier = identifier
    if type is not None:
        asset.type = type
    if status is not None:
        asset.status = status
    db.add(asset)
    db.flush()
    return asset


def delete_asset(db: Session, asset: Asset) -> None:
    db.delete(asset)
