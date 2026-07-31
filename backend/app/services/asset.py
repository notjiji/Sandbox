import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.asset import Asset
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.repositories.asset import (
    create_asset,
    delete_asset,
    get_asset_by_id,
    list_assets_for_project,
    update_asset,
)
from app.repositories.project import get_project_by_id
from app.schemas.asset import AssetListResponse, AssetSummary, CreateAssetRequest, UpdateAssetRequest
from app.services.audit import AuditAction, record_audit_event


def _get_active_project(
    db: Session,
    membership: OrganizationMember,
    project_id: uuid.UUID,
) -> Project:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project or not project.is_active:
        raise NotFoundError("Project")
    return project


def _to_asset_summary(asset: Asset) -> AssetSummary:
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
    _get_active_project(db, membership, project_id)
    assets = list_assets_for_project(db, project_id=project_id)
    items = [_to_asset_summary(asset) for asset in assets]
    return AssetListResponse(items=items, total=len(items))


def create_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: CreateAssetRequest,
) -> AssetSummary:
    _get_active_project(db, membership, project_id)
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
        action=AuditAction.ASSET_CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="asset",
        resource_id=asset.id,
        details={"project_id": str(project_id), "name": asset.name},
    )
    db.commit()
    db.refresh(asset)
    return _to_asset_summary(asset)


def get_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetSummary:
    _get_active_project(db, membership, project_id)
    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")
    return _to_asset_summary(asset)


def update_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: UpdateAssetRequest,
) -> AssetSummary:
    _get_active_project(db, membership, project_id)
    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")

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
        action=AuditAction.ASSET_UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="asset",
        resource_id=asset.id,
        details=body.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(asset)
    return _to_asset_summary(asset)


def delete_project_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    _get_active_project(db, membership, project_id)
    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")

    delete_asset(db, asset)
    record_audit_event(
        db,
        action=AuditAction.ASSET_DELETE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="asset",
        resource_id=asset.id,
    )
    db.commit()
