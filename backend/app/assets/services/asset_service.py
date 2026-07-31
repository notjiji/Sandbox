import uuid

from sqlalchemy.orm import Session

from app.assets.events import AssetAuditAction
from app.assets.models import Asset
from app.assets.repository import (
    create_asset,
    delete_asset,
    get_asset_by_id,
    list_assets_for_project,
    update_asset,
)
from app.assets.schemas import AssetListResponse, AssetSummary, CreateAssetRequest, UpdateAssetRequest
from app.assets.validators import require_active_project, validate_create_payload, validate_update_payload
from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.audit.service import record_audit_event


def to_asset_summary(asset: Asset) -> AssetSummary:
    return AssetSummary(
        id=str(asset.id),
        project_id=str(asset.project_id),
        name=asset.name,
        identifier=asset.identifier,
        type=asset.type,
        status=asset.status,
        created_by=str(asset.created_by) if asset.created_by else None,
    )


def list_project_assets(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> AssetListResponse:
    require_active_project(db, membership, project_id)
    assets = list_assets_for_project(db, project_id=project_id)
    items = [to_asset_summary(asset) for asset in assets]
    return AssetListResponse(items=items, total=len(items))


def create_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: CreateAssetRequest,
) -> AssetSummary:
    validate_create_payload(body)
    require_active_project(db, membership, project_id)
    asset = create_asset(
        db,
        project_id=project_id,
        name=body.name,
        identifier=body.identifier,
        type=body.type,
        created_by=membership.user_id,
    )
    record_audit_event(
        db,
        action=AssetAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="asset",
        resource_id=asset.id,
        details={"project_id": str(project_id), "name": asset.name},
    )
    db.commit()
    db.refresh(asset)
    return to_asset_summary(asset)


def get_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetSummary:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")
    return to_asset_summary(asset)


def update_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: UpdateAssetRequest,
) -> AssetSummary:
    validate_update_payload(body)
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")

    update_asset(
        db,
        asset,
        name=body.name,
        identifier=body.identifier,
        type=body.type,
        status=body.status,
    )
    record_audit_event(
        db,
        action=AssetAuditAction.UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="asset",
        resource_id=asset.id,
        details=body.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(asset)
    return to_asset_summary(asset)


def delete_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")

    delete_asset(db, asset)
    record_audit_event(
        db,
        action=AssetAuditAction.DELETE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="asset",
        resource_id=asset.id,
    )
    db.commit()
