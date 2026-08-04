import uuid

from sqlalchemy.orm import Session, joinedload

from app.assets.enums import AssetLinkType
from app.assets.link_models import AssetLink
from app.assets.models import Asset


def list_links_for_asset(
    db: Session,
    *,
    asset_id: uuid.UUID,
) -> tuple[list[AssetLink], list[AssetLink]]:
    outbound = (
        db.query(AssetLink)
        .options(
            joinedload(AssetLink.target_asset).joinedload(Asset.metadata_entries),
            joinedload(AssetLink.target_asset).joinedload(Asset.tags),
        )
        .filter(AssetLink.source_asset_id == asset_id)
        .order_by(AssetLink.created_at.asc())
        .all()
    )
    inbound = (
        db.query(AssetLink)
        .options(
            joinedload(AssetLink.source_asset).joinedload(Asset.metadata_entries),
            joinedload(AssetLink.source_asset).joinedload(Asset.tags),
        )
        .filter(AssetLink.target_asset_id == asset_id)
        .order_by(AssetLink.created_at.asc())
        .all()
    )
    return outbound, inbound


def get_link_by_id(
    db: Session,
    *,
    link_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> AssetLink | None:
    return (
        db.query(AssetLink)
        .filter(
            AssetLink.id == link_id,
            AssetLink.organization_id == organization_id,
        )
        .first()
    )


def create_link(
    db: Session,
    *,
    organization_id: uuid.UUID,
    source_asset_id: uuid.UUID,
    target_asset_id: uuid.UUID,
    link_type: AssetLinkType,
    label: str | None = None,
) -> AssetLink:
    link = AssetLink(
        organization_id=organization_id,
        source_asset_id=source_asset_id,
        target_asset_id=target_asset_id,
        link_type=link_type,
        label=label,
    )
    db.add(link)
    db.flush()
    return link


def delete_link(db: Session, link: AssetLink) -> None:
    db.delete(link)
    db.flush()
