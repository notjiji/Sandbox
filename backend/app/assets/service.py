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
from app.assets.metadata import build_asset_metadata, metadata_to_dict, resolve_primary_value
from app.assets.models import Asset
from app.assets.repositories.asset_repository import (
    archive_asset,
    create_asset,
    get_asset_by_id,
    list_assets_for_project,
    list_child_assets,
    replace_tags,
    restore_asset,
    soft_delete_asset,
    update_asset,
    upsert_metadata_entries,
)
from app.assets.schemas import (
    AssetListQuery,
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
    validate_archivable,
    validate_asset_metadata_for_update,
    validate_asset_scannable,
    validate_create_payload,
    validate_hierarchy,
    validate_parent_type,
    validate_restorable,
    validate_update_payload,
)
from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.plugins.base import ScanTarget


class AssetService:
    """Owns everything related to digital assets within a project."""

    def to_summary(self, asset: Asset, *, children_count: int = 0) -> AssetSummary:
        metadata = metadata_to_dict(asset.metadata_entries)
        tags = [entry.tag for entry in asset.tags]
        return AssetSummary(
            id=str(asset.id),
            organization_id=str(asset.organization_id),
            project_id=str(asset.project_id),
            parent_id=str(asset.parent_id) if asset.parent_id else None,
            name=asset.name,
            description=asset.description,
            type=asset.type,
            status=asset.status,
            environment=asset.environment,
            criticality=asset.criticality,
            owner=asset.owner,
            metadata=metadata,
            tags=tags,
            created_by=str(asset.created_by) if asset.created_by else None,
            children_count=children_count,
        )

    def list_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        query: AssetListQuery | None = None,
    ) -> AssetListResponse:
        require_active_project(db, membership, project_id)
        params = query or AssetListQuery()
        assets, total = list_assets_for_project(
            db,
            project_id=project_id,
            page=params.page,
            limit=params.limit,
            status=params.status,
            asset_type=params.type,
            criticality=params.criticality,
            environment=params.environment,
            search=params.search,
        )
        child_counts = {
            asset.id: len(list_child_assets(db, parent_id=asset.id))
            for asset in assets
            if asset.type in PARENT_ASSET_TYPES
        }
        items = [
            self.to_summary(asset, children_count=child_counts.get(asset.id, 0))
            for asset in assets
        ]
        return AssetListResponse(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
        )

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
        project = require_active_project(db, membership, project_id)
        parent_id = self._resolve_parent(db, project_id=project_id, body=body)

        asset = create_asset(
            db,
            organization_id=project.organization_id,
            project_id=project_id,
            parent_id=parent_id,
            name=body.name,
            description=body.description,
            type=body.type,
            status=body.status,
            environment=body.environment,
            criticality=body.criticality,
            owner=body.owner,
            created_by=membership.user_id,
        )
        upsert_metadata_entries(db, asset_id=asset.id, metadata=body.metadata)
        replace_tags(db, asset_id=asset.id, tags=body.tags)
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.CREATE,
            asset=asset,
            details={"project_id": str(project_id), "name": asset.name, "type": asset.type.value},
        )
        db.commit()
        reloaded = get_asset_by_id(db, project_id=project_id, asset_id=asset.id)
        if not reloaded:
            raise NotFoundError("Asset")
        return self.to_summary(reloaded)

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
        validate_asset_metadata_for_update(
            body,
            asset_type=asset.type,
            existing_metadata=metadata_to_dict(asset.metadata_entries),
        )

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
            description=body.description,
            type=body.type,
            status=body.status,
            environment=body.environment,
            criticality=body.criticality,
            owner=body.owner,
            parent_id=parent_uuid,
            clear_parent=clear_parent,
        )
        if body.metadata is not None:
            upsert_metadata_entries(db, asset_id=asset.id, metadata=body.metadata)
        if body.tags is not None:
            replace_tags(db, asset_id=asset.id, tags=body.tags)
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.UPDATE,
            asset=asset,
            details=body.model_dump(exclude_none=True),
        )
        db.commit()
        reloaded = get_asset_by_id(db, project_id=project_id, asset_id=asset.id)
        if not reloaded:
            raise NotFoundError("Asset")
        return self.to_summary(reloaded)

    def delete_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> None:
        asset = self._get_asset_entity(db, membership, project_id=project_id, asset_id=asset_id)
        soft_delete_asset(db, asset)
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.DELETE,
            asset=asset,
        )
        db.commit()

    def archive_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetSummary:
        asset = self._get_asset_entity(db, membership, project_id=project_id, asset_id=asset_id)
        validate_archivable(asset)
        archive_asset(db, asset)
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.ARCHIVE,
            asset=asset,
        )
        db.commit()
        reloaded = get_asset_by_id(db, project_id=project_id, asset_id=asset.id)
        if not reloaded:
            raise NotFoundError("Asset")
        return self.to_summary(reloaded)

    def restore_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetSummary:
        require_active_project(db, membership, project_id)
        asset = get_asset_by_id(
            db,
            project_id=project_id,
            asset_id=asset_id,
            include_deleted=True,
        )
        if not asset:
            raise NotFoundError("Asset")
        validate_restorable(asset)
        restore_asset(db, asset)
        self._record_event(
            db,
            membership,
            action=AssetAuditAction.RESTORE,
            asset=asset,
        )
        db.commit()
        reloaded = get_asset_by_id(db, project_id=project_id, asset_id=asset.id)
        if not reloaded:
            raise NotFoundError("Asset")
        return self.to_summary(reloaded)

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
        validate_asset_scannable(asset)

        children = (
            list_child_assets(db, parent_id=asset.id)
            if asset.type in PARENT_ASSET_TYPES
            else []
        )
        metadata = metadata_to_dict(asset.metadata_entries)
        child_metadata = {
            str(child.id): metadata_to_dict(child.metadata_entries) for child in children
        }
        scan_metadata = build_asset_metadata(
            asset,
            metadata=metadata,
            children=children,
            child_metadata=child_metadata,
        )
        related = [
            RelatedScanTarget(
                asset_id=str(child.id),
                identifier=resolve_primary_value(child, child_metadata[str(child.id)]),
                asset_type=child.type,
            )
            for child in children
        ]

        return ScanTargetContext(
            asset_id=str(asset.id),
            project_id=str(asset.project_id),
            name=asset.name,
            identifier=resolve_primary_value(asset, metadata),
            asset_type=asset.type,
            parent_id=str(asset.parent_id) if asset.parent_id else None,
            environment=asset.environment,
            criticality=asset.criticality,
            metadata=scan_metadata,
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

    def require_scannable_asset(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Asset:
        asset = self._get_asset_entity(db, membership, project_id=project_id, asset_id=asset_id)
        validate_asset_scannable(asset)
        return asset

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
archive_project_asset = asset_service.archive_for_project
restore_project_asset = asset_service.restore_for_project
