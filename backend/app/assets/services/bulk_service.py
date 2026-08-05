"""Bulk asset operations."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.bulk_enums import AssetBulkAction
from app.assets.events import AssetAuditAction
from app.assets.repositories.asset_repository import (
    archive_asset,
    get_asset_by_id,
    merge_tags,
    replace_tags,
    soft_delete_asset,
    update_asset,
)
from app.assets.schemas import (
    AssetBulkActionItemResult,
    AssetBulkActionRequest,
    AssetBulkActionResponse,
)
from app.assets.services.asset_service import asset_service
from app.assets.validators import require_active_project, validate_archivable, validate_updatable
from app.core.exceptions import ValidationAppError
from app.members.models import OrganizationMember
from app.scans.schemas import CreateAssetScanRequest
from app.scans.services import scan_service


def _parse_asset_ids(asset_ids: list[str]) -> list[uuid.UUID]:
    parsed: list[uuid.UUID] = []
    seen: set[uuid.UUID] = set()
    for raw in asset_ids:
        try:
            asset_id = uuid.UUID(raw)
        except ValueError as exc:
            raise ValidationAppError(f"Invalid asset id: {raw}") from exc
        if asset_id in seen:
            continue
        seen.add(asset_id)
        parsed.append(asset_id)
    if not parsed:
        raise ValidationAppError("At least one asset id is required")
    return parsed


def _result(
    asset_id: uuid.UUID,
    *,
    success: bool,
    message: str | None = None,
    scan_id: str | None = None,
) -> AssetBulkActionItemResult:
    return AssetBulkActionItemResult(
        asset_id=str(asset_id),
        success=success,
        message=message,
        scan_id=scan_id,
    )


def execute_bulk_action(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: AssetBulkActionRequest,
) -> AssetBulkActionResponse:
    require_active_project(db, membership, project_id)
    try:
        action = AssetBulkAction(body.action)
    except ValueError as exc:
        raise ValidationAppError(f"Unknown bulk action: {body.action}") from exc

    asset_ids = _parse_asset_ids(body.asset_ids)
    results: list[AssetBulkActionItemResult] = []
    export_assets = []

    if action == AssetBulkAction.ASSIGN_TAGS and not body.tags:
        raise ValidationAppError("tags are required for assign_tags")
    if action == AssetBulkAction.CHANGE_OWNER and not (body.owner and body.owner.strip()):
        raise ValidationAppError("owner is required for change_owner")

    for asset_id in asset_ids:
        if action == AssetBulkAction.LAUNCH_SCAN:
            try:
                asset_service.require_scannable_asset(
                    db, membership, project_id=project_id, asset_id=asset_id
                )
                scan = scan_service.create_asset_scan(
                    db,
                    membership,
                    project_id=project_id,
                    asset_id=asset_id,
                    body=CreateAssetScanRequest(scan_type=body.scan_type),
                )
                scan = scan_service.run_asset_scan(
                    db,
                    membership,
                    project_id=project_id,
                    asset_id=asset_id,
                    scan_id=uuid.UUID(scan.id),
                )
                results.append(_result(asset_id, success=True, scan_id=scan.id))
            except Exception as exc:
                message = str(exc) if str(exc) else exc.__class__.__name__
                results.append(_result(asset_id, success=False, message=message))
            continue

        savepoint = db.begin_nested()
        try:
            asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
            if not asset:
                savepoint.rollback()
                results.append(_result(asset_id, success=False, message="Asset not found"))
                continue

            if action == AssetBulkAction.EXPORT:
                export_assets.append(asset)
                savepoint.commit()
                results.append(_result(asset_id, success=True))
                continue

            if action == AssetBulkAction.ARCHIVE:
                validate_archivable(asset)
                archive_asset(db, asset, archived_by=membership.user_id)
                asset_service._record_event(
                    db, membership, action=AssetAuditAction.ARCHIVE, asset=asset
                )
                savepoint.commit()
                results.append(_result(asset_id, success=True))
                continue

            if action == AssetBulkAction.DELETE:
                soft_delete_asset(db, asset)
                asset_service._record_event(
                    db, membership, action=AssetAuditAction.DELETE, asset=asset
                )
                savepoint.commit()
                results.append(_result(asset_id, success=True))
                continue

            validate_updatable(asset)

            if action == AssetBulkAction.ASSIGN_TAGS:
                if body.tag_mode == "replace":
                    replace_tags(db, asset_id=asset.id, tags=body.tags)
                else:
                    merge_tags(db, asset_id=asset.id, tags=body.tags)
                asset_service._record_event(
                    db,
                    membership,
                    action=AssetAuditAction.UPDATE,
                    asset=asset,
                    details={"bulk_action": "assign_tags", "tags": body.tags},
                )
                savepoint.commit()
                results.append(_result(asset_id, success=True))
                continue

            if action == AssetBulkAction.CHANGE_OWNER:
                owner = body.owner.strip() if body.owner else ""
                update_asset(db, asset, owner=owner, updated_by=membership.user_id)
                asset_service._record_event(
                    db,
                    membership,
                    action=AssetAuditAction.UPDATE,
                    asset=asset,
                    details={"bulk_action": "change_owner", "owner": owner},
                )
                savepoint.commit()
                results.append(_result(asset_id, success=True))
                continue

            savepoint.rollback()
            results.append(_result(asset_id, success=False, message="Unsupported action"))
        except Exception as exc:
            savepoint.rollback()
            message = str(exc) if str(exc) else exc.__class__.__name__
            results.append(_result(asset_id, success=False, message=message))

    succeeded = sum(1 for item in results if item.success)
    failed = len(results) - succeeded
    if succeeded and action != AssetBulkAction.LAUNCH_SCAN:
        db.commit()

    export_items = (
        asset_service._summaries_for_assets(db, export_assets)
        if action == AssetBulkAction.EXPORT
        else []
    )

    return AssetBulkActionResponse(
        action=action.value,
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        results=results,
        export_items=export_items,
    )
