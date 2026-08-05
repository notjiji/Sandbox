"""Asset Service — single owner of digital asset domain logic."""

import uuid

from sqlalchemy.orm import Session

from app.assets.enums import (
    DEFAULT_ASSET_CATEGORY_BY_TYPE,
    OPTIONAL_PARENT_TYPES,
    PARENT_ASSET_TYPES,
    PURE_ROOT_TYPES,
    REQUIRED_PARENT_TYPES,
    AssetType,
    CHILD_ASSET_TYPES,
    ROOT_ASSET_TYPES,
)
from app.assets.events import AssetAuditAction
from app.assets.adapter import asset_adapter
from app.assets.metadata import metadata_to_dict, resolve_external_identifier
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
    AssetActorSummary,
    AssetChildrenResponse,
    AssetListQuery,
    AssetListResponse,
    AssetSummary,
    CreateAssetRequest,
    NormalizedScanTarget,
    UpdateAssetRequest,
)
from app.assets.services.asset_enrichment import (
    AssetSecurityStats,
    card_last_scan,
    card_security_score,
    compute_health_status,
    load_security_stats_batch,
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
    validate_updatable,
    validate_update_payload,
)
from app.audit.repositories.audit_repository import list_audit_logs_for_resource
from app.audit.schemas import AuditLogListResponse, AuditLogSummary
from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.plugins.base.plugin import ScanTarget
from app.users.models import User


def _user_to_actor(user: User | None) -> AssetActorSummary | None:
    if not user:
        return None
    name = f"{user.first_name} {user.last_name}".strip()
    return AssetActorSummary(
        id=str(user.id),
        name=name or None,
        email=user.email,
    )


class AssetService:
    """Owns everything related to digital assets within a project."""

    def to_summary(
        self,
        asset: Asset,
        *,
        children_count: int = 0,
        security: AssetSecurityStats | None = None,
    ) -> AssetSummary:
        metadata = metadata_to_dict(asset.metadata_entries)
        tags = [entry.tag for entry in asset.tags]
        security = security or AssetSecurityStats()
        health_status = compute_health_status(asset.status, security)
        last_scan = card_last_scan(security)
        security_score = card_security_score(security)
        return AssetSummary(
            id=str(asset.id),
            organization_id=str(asset.organization_id),
            organization_name=asset.organization.name if asset.organization else None,
            project_id=str(asset.project_id),
            project_name=asset.project.name if asset.project else None,
            parent_id=str(asset.parent_id) if asset.parent_id else None,
            parent_name=asset.parent.name if asset.parent else None,
            name=asset.name,
            description=asset.description,
            notes=asset.notes,
            type=asset.type,
            external_identifier=asset.external_identifier,
            status=asset.status,
            environment=asset.environment,
            criticality=asset.criticality,
            business_unit=asset.business_unit,
            owner=asset.owner,
            asset_category=asset.asset_category,
            metadata=metadata,
            tags=tags,
            children_count=children_count,
            current_risk_score=security.current_risk_score,
            security_grade=security.security_grade,
            last_scan_at=security.last_scan_at,
            last_successful_scan_at=security.last_successful_scan_at,
            last_scan_status=security.last_scan_status,
            findings_count=security.findings_count,
            critical_findings_count=security.critical_findings_count,
            security_score=security_score,
            critical_findings=security.critical_findings_count,
            last_scan=last_scan,
            next_scan=security.next_scan_at,
            health_status=health_status,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            archived_at=asset.archived_at,
            archived_by=_user_to_actor(asset.archiver),
            created_by=_user_to_actor(asset.creator),
            last_modified_by=_user_to_actor(asset.updater),
        )

    def summary_for_asset(
        self,
        db: Session,
        asset: Asset,
        *,
        children_count: int | None = None,
    ) -> AssetSummary:
        if children_count is None:
            children_count = (
                len(list_child_assets(db, parent_id=asset.id))
                if asset.type in PARENT_ASSET_TYPES
                else 0
            )
        security = load_security_stats_batch(
            db,
            organization_id=asset.organization_id,
            asset_ids=[asset.id],
        ).get(asset.id)
        return self.to_summary(asset, children_count=children_count, security=security)

    def _summaries_for_assets(
        self,
        db: Session,
        assets: list[Asset],
        *,
        child_counts: dict[uuid.UUID, int] | None = None,
    ) -> list[AssetSummary]:
        if not assets:
            return []
        organization_id = assets[0].organization_id
        asset_ids = [asset.id for asset in assets]
        security_by_asset = load_security_stats_batch(
            db,
            organization_id=organization_id,
            asset_ids=asset_ids,
        )
        child_counts = child_counts or {}
        return [
            self.to_summary(
                asset,
                children_count=child_counts.get(asset.id, 0),
                security=security_by_asset.get(asset.id),
            )
            for asset in assets
        ]

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
        parent_uuid = parse_parent_id(params.parent_id) if params.parent_id else None
        assets, total = list_assets_for_project(
            db,
            project_id=project_id,
            page=params.page,
            limit=params.limit,
            status=params.status,
            asset_type=params.type,
            criticality=params.criticality,
            environment=params.environment,
            asset_category=params.asset_category,
            search=params.search,
            tags=params.tags,
            sort=params.sort,
            order=params.order,
            roots_only=params.roots_only,
            parent_id=parent_uuid,
        )
        child_counts = {
            asset.id: len(list_child_assets(db, parent_id=asset.id))
            for asset in assets
            if asset.type in PARENT_ASSET_TYPES
        }
        items = self._summaries_for_assets(db, assets, child_counts=child_counts)
        return AssetListResponse(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def list_children_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        parent_id: uuid.UUID,
        query: AssetListQuery | None = None,
    ) -> AssetChildrenResponse:
        require_active_project(db, membership, project_id)
        parent = get_asset_by_id(db, project_id=project_id, asset_id=parent_id)
        if not parent:
            raise NotFoundError("Asset")

        params = query or AssetListQuery()
        children = list_child_assets(
            db,
            parent_id=parent_id,
            status=params.status,
            asset_type=params.type,
            criticality=params.criticality,
            environment=params.environment,
            asset_category=params.asset_category,
            search=params.search,
            tags=params.tags,
            sort=params.sort,
            order=params.order,
        )
        items = self._summaries_for_assets(db, children)
        return AssetChildrenResponse(items=items, total=len(items))

    def get_for_project(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AssetSummary:
        asset = self._get_asset_entity(
            db,
            membership,
            project_id=project_id,
            asset_id=asset_id,
            include_deleted=True,
        )
        return self.summary_for_asset(db, asset)

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
        asset_category = body.asset_category or DEFAULT_ASSET_CATEGORY_BY_TYPE.get(body.type)

        asset = create_asset(
            db,
            organization_id=project.organization_id,
            project_id=project_id,
            parent_id=parent_id,
            name=body.name,
            description=body.description,
            notes=body.notes,
            type=body.type,
            status=body.status,
            environment=body.environment,
            criticality=body.criticality,
            owner=body.owner,
            external_identifier=body.external_identifier,
            business_unit=body.business_unit,
            asset_category=asset_category,
            created_by=membership.user_id,
        )
        upsert_metadata_entries(db, asset_id=asset.id, metadata=body.metadata)
        if not asset.external_identifier:
            metadata = metadata_to_dict(asset.metadata_entries)
            external_id = resolve_external_identifier(
                body.type,
                metadata,
                explicit=body.external_identifier,
                fallback_name=body.name,
            )
            if external_id:
                asset.external_identifier = external_id
                db.add(asset)
                db.flush()
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
        return self.summary_for_asset(db, reloaded)

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
        validate_updatable(asset)
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
        if next_type in PURE_ROOT_TYPES:
            clear_parent = True
        elif next_type in REQUIRED_PARENT_TYPES:
            resolved_parent = body.parent_id if body.parent_id is not None else next_parent_id
            parent_uuid = self._resolve_parent_id(
                db,
                project_id=project_id,
                child_type=next_type,
                parent_id=resolved_parent,
            )
        elif next_type in OPTIONAL_PARENT_TYPES:
            if body.parent_id is not None:
                parent_uuid = self._resolve_parent_id(
                    db,
                    project_id=project_id,
                    child_type=next_type,
                    parent_id=body.parent_id,
                )
        else:
            clear_parent = True

        update_asset(
            db,
            asset,
            name=body.name,
            description=body.description,
            notes=body.notes,
            type=body.type,
            status=body.status,
            environment=body.environment,
            criticality=body.criticality,
            owner=body.owner,
            external_identifier=body.external_identifier,
            business_unit=body.business_unit,
            asset_category=body.asset_category,
            updated_by=membership.user_id,
            parent_id=parent_uuid,
            clear_parent=clear_parent,
        )
        if body.metadata is not None:
            upsert_metadata_entries(db, asset_id=asset.id, metadata=body.metadata)
        if body.external_identifier is None and body.metadata is not None:
            metadata = metadata_to_dict(asset.metadata_entries)
            external_id = resolve_external_identifier(
                next_type,
                metadata,
                fallback_name=asset.name,
            )
            asset.external_identifier = external_id
            db.add(asset)
            db.flush()
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
        return self.summary_for_asset(db, reloaded)

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
        archive_asset(db, asset, archived_by=membership.user_id)
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
        return self.summary_for_asset(db, reloaded)

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
        return self.summary_for_asset(db, reloaded)

    def list_audit_history(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        limit: int = 50,
    ) -> AuditLogListResponse:
        self._get_asset_entity(
            db,
            membership,
            project_id=project_id,
            asset_id=asset_id,
            include_deleted=True,
        )
        logs = list_audit_logs_for_resource(
            db,
            resource_type="asset",
            resource_id=asset_id,
            limit=limit,
        )
        items = [
            AuditLogSummary(
                id=str(log.id),
                action=log.action,
                user_id=str(log.user_id) if log.user_id else None,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ]
        return AuditLogListResponse(items=items, total=len(items))

    def get_scan_target(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> NormalizedScanTarget:
        """Return scan-ready asset information for the Scan Engine."""
        return asset_adapter.adapt(db, project_id=project_id, asset_id=asset_id)

    def resolve_plugin_targets(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> list[ScanTarget]:
        """Translate asset domain data into plugin scan targets."""
        return asset_adapter.resolve_targets(db, project_id=project_id, asset_id=asset_id)

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
        include_deleted: bool = False,
    ) -> Asset:
        require_active_project(db, membership, project_id)
        asset = get_asset_by_id(
            db,
            project_id=project_id,
            asset_id=asset_id,
            include_deleted=include_deleted,
        )
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
        if body.type in PURE_ROOT_TYPES:
            return None
        if body.type in OPTIONAL_PARENT_TYPES and not body.parent_id:
            return None
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
list_project_asset_children = asset_service.list_children_for_project
get_project_asset = asset_service.get_for_project
create_project_asset = asset_service.create_for_project
update_project_asset = asset_service.update_for_project
delete_project_asset = asset_service.delete_for_project
archive_project_asset = asset_service.archive_for_project
restore_project_asset = asset_service.restore_for_project
list_asset_audit_history = asset_service.list_audit_history
