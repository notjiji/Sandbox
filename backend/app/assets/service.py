"""Asset Service — single owner of digital asset domain logic."""

import uuid

from sqlalchemy.orm import Session

from app.assets.enums import (
    AssetType,
    CHILD_ASSET_TYPES,
    PARENT_ASSET_TYPES,
    ROOT_ASSET_TYPES,
)
from app.assets.events import AssetAuditAction
from app.assets.metadata import build_asset_metadata
from app.assets.models import Asset
from app.assets.repositories.asset_repository import (
    create_asset,
    delete_asset,
    get_asset_by_id,
    list_assets_for_project,
    list_child_assets,
    update_asset,
)
from app.assets.schemas import (
    AssetListResponse,
    AssetSummary,
    CreateAssetRequest,
    RelatedScanTarget,
    ScanTargetContext,
    UpdateAssetRequest,
)
from app.assets.validators import (
    parse_parent_id,
    require_active_project,
    validate_create_payload,
    validate_hierarchy,
    validate_parent_type,
    validate_update_payload,
)
from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.plugins.base import ScanTarget


class AssetService:
    """Owns everything related to digital assets within a project."""

    def to_summary(self, asset: Asset, *, children_count: int = 0) -> AssetSummary:
        return AssetSummary(
            id=str(asset.id),
            project_id=str(asset.project_id),
            parent_id=str(asset.parent_id) if asset.parent_id else None,
            name=asset.name,
            identifier=asset.identifier,
            type=asset.type,
            status=asset.status,
            created_by=str(asset.created_by) if asset.created_by else None,
            children_count=children_count,
        )

    def list_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
    ) -> AssetListResponse:
        require_active_project(db, membership, project_id)
        assets = list_assets_for_project(db, project_id=project_id)
        child_counts = {
            asset.id: len(list_child_assets(db, parent_id=asset.id))
            for asset in assets
            if asset.type in PARENT_ASSET_TYPES
        }
        items = [
            self.to_summary(asset, children_count=child_counts.get(asset.id, 0))
            for asset in assets
        ]
        return AssetListResponse(items=items, total=len(items))

    def get_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetSummary:
        asset = self._get_asset_entity(db, membership, project_id=project_id, asset_id=asset_id)
        children_count = 0
        if asset.type in PARENT_ASSET_TYPES:
            children_count = len(list_child_assets(db, parent_id=asset.id))
        return self.to_summary(asset, children_count=children_count)

    def create_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        body: CreateAssetRequest,
    ) -> AssetSummary:
        validate_create_payload(body)
        require_active_project(db, membership, project_id)
        parent_id = self._resolve_parent(db, project_id=project_id, body=body)

        asset = create_asset(
            db,
            project_id=project_id,
            parent_id=parent_id,
            name=body.name,
            identifier=body.identifier,
            type=body.type,
            created_by=membership.user_id,
        )
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.CREATE,
            asset=asset,
            details={"project_id": str(project_id), "name": asset.name, "type": asset.type.value},
        )
        db.commit()
        db.refresh(asset)
        return self.to_summary(asset)

    def update_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        body: UpdateAssetRequest,
    ) -> AssetSummary:
        validate_update_payload(body)
        asset = self._get_asset_entity(db, membership, project_id=project_id, asset_id=asset_id)

        next_type = body.type or asset.type
        next_parent_id = body.parent_id if body.parent_id is not None else (
            str(asset.parent_id) if asset.parent_id else None
        )
        validate_hierarchy(next_type, next_parent_id)

        parent_uuid = None
        clear_parent = False
        if next_type in ROOT_ASSET_TYPES:
            clear_parent = True
        elif body.parent_id is not None:
            parent_uuid = self._resolve_parent_id(
                db,
                project_id=project_id,
                child_type=next_type,
                parent_id=body.parent_id,
            )

        update_asset(
            db,
            asset,
            name=body.name,
            identifier=body.identifier,
            type=body.type,
            status=body.status,
            parent_id=parent_uuid,
            clear_parent=clear_parent,
        )
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.UPDATE,
            asset=asset,
            details=body.model_dump(exclude_none=True),
        )
        db.commit()
        db.refresh(asset)
        return self.to_summary(asset)

    def delete_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> None:
        asset = self._get_asset_entity(db, membership, project_id=project_id, asset_id=asset_id)
        delete_asset(db, asset)
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.DELETE,
            asset=asset,
        )
        db.commit()

    def get_scan_target(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> ScanTargetContext:
        """Return scan-ready asset information for the Scan Engine."""
        asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
        if not asset:
            raise NotFoundError("Asset")

        children = (
            list_child_assets(db, parent_id=asset.id)
            if asset.type in PARENT_ASSET_TYPES
            else []
        )
        metadata = build_asset_metadata(asset, children=children)
        related = [
            RelatedScanTarget(
                asset_id=str(child.id),
                identifier=child.identifier or child.name,
                asset_type=child.type,
            )
            for child in children
        ]

        return ScanTargetContext(
            asset_id=str(asset.id),
            project_id=str(asset.project_id),
            name=asset.name,
            identifier=asset.identifier or asset.name,
            asset_type=asset.type,
            parent_id=str(asset.parent_id) if asset.parent_id else None,
            metadata=metadata,
            related_targets=related,
        )

    def resolve_plugin_targets(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> list[ScanTarget]:
        """Translate asset domain data into plugin scan targets."""
        context = self.get_scan_target(db, project_id=project_id, asset_id=asset_id)
        targets = [
            ScanTarget(
                asset_id=context.asset_id,
                identifier=context.identifier,
                asset_type=context.asset_type.value,
            )
        ]
        for related in context.related_targets:
            targets.append(
                ScanTarget(
                    asset_id=related.asset_id,
                    identifier=related.identifier,
                    asset_type=related.asset_type.value,
                )
            )
        return targets

    def _get_asset_entity(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Asset:
        require_active_project(db, membership, project_id)
        asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
        if not asset:
            raise NotFoundError("Asset")
        return asset

    def _resolve_parent(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        body: CreateAssetRequest,
    ) -> uuid.UUID | None:
        if body.type not in CHILD_ASSET_TYPES:
            return None
        parent_id = self._resolve_parent_id(
            db,
            project_id=project_id,
            child_type=body.type,
            parent_id=body.parent_id,
        )
        if not parent_id:
            raise NotFoundError("Parent asset")
        return parent_id

    def _resolve_parent_id(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        child_type: AssetType,
        parent_id: str | None,
    ) -> uuid.UUID | None:
        parent_uuid = parse_parent_id(parent_id)
        if not parent_uuid:
            return None
        parent = get_asset_by_id(db, project_id=project_id, asset_id=parent_uuid)
        if not parent:
            raise NotFoundError("Parent asset")
        validate_parent_type(child_type, parent.type)
        return parent_uuid

    def _record_event(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        action: str,
        asset: Asset,
        details: dict | None = None,
    ) -> None:
        record_audit_event(
            db,
            action=action,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="asset",
            resource_id=asset.id,
            details=details,
        )


asset_service = AssetService()

# Backward-compatible function aliases for existing imports.
list_project_assets = asset_service.list_for_project
get_project_asset = asset_service.get_for_project
create_project_asset = asset_service.create_for_project
update_project_asset = asset_service.update_for_project
delete_project_asset = asset_service.delete_for_project
