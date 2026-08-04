import uuid

from sqlalchemy.orm import Session

from app.assets.services.asset_service import asset_service
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember
from app.plugins.builtin import discover_plugins
from app.plugins.registry import registry
from app.scans.enums import ScanStatus, ScanType
from app.scans.events import ScanAuditAction
from app.scans.lifecycle import lifecycle_timestamps, transition_scan_status
from app.scans.models import Scan
from app.scans.profiles import list_scan_profiles, resolve_profile_plugins
from app.scans.repositories.scan_plugin_repository import list_plugin_runs_for_scan
from app.scans.repositories.scan_repository import (
    create_scan,
    get_scan_for_asset,
    list_scans_for_asset,
)
from app.scans.schemas import (
    CreateAssetScanRequest,
    ScanLifecycleTimestamps,
    ScanListResponse,
    ScanPluginRunSummary,
    ScanProfileListResponse,
    ScanProfileSummary,
    ScanSummary,
)
from app.scans.services.scan_executor import run_queued_scan as _run_queued_scan
from app.audit.service import record_audit_event


def _ensure_plugins_loaded() -> None:
    if not registry.list_names():
        discover_plugins(registry)


def _validate_create_scan(body: CreateAssetScanRequest) -> list[str] | None:
    if body.scan_type == ScanType.CUSTOM:
        if not body.plugins:
            raise ValidationAppError("Custom scans require at least one plugin")
        selected = resolve_profile_plugins(body.scan_type, body.plugins)
        _ensure_plugins_loaded()
        _, missing = registry.resolve_plugin_names(selected)
        if missing:
            raise ValidationAppError(f"Unknown or disabled plugin(s): {', '.join(missing)}")
        return selected

    if body.plugins:
        raise ValidationAppError("plugins may only be set for custom scans")
    resolve_profile_plugins(body.scan_type)
    return None


def _profile_plugins_for_scan(scan: Scan) -> list[str]:
    try:
        return resolve_profile_plugins(scan.scan_type, scan.selected_plugins)
    except ValidationAppError:
        return list(scan.selected_plugins or [])


def to_plugin_run_summary(plugin_run) -> ScanPluginRunSummary:
    return ScanPluginRunSummary(
        id=str(plugin_run.id),
        asset_id=str(plugin_run.asset_id),
        plugin_name=plugin_run.plugin_name,
        status=plugin_run.status,
        error_message=plugin_run.error_message,
        findings_count=plugin_run.findings_count,
        duration_seconds=plugin_run.duration_seconds,
        metadata=plugin_run.metadata_json or {},
        started_at=plugin_run.started_at,
        completed_at=plugin_run.completed_at,
    )


def to_scan_summary(scan: Scan, *, include_plugin_runs: bool = False) -> ScanSummary:
    plugin_runs = []
    if include_plugin_runs and hasattr(scan, "plugin_runs"):
        plugin_runs = [to_plugin_run_summary(run) for run in scan.plugin_runs]
    selected_plugins = list(scan.selected_plugins or [])
    return ScanSummary(
        id=str(scan.id),
        project_id=str(scan.project_id),
        asset_id=str(scan.asset_id),
        status=scan.status,
        scan_type=scan.scan_type,
        selected_plugins=selected_plugins,
        profile_plugins=_profile_plugins_for_scan(scan),
        created_by=str(scan.created_by) if scan.created_by else None,
        lifecycle=ScanLifecycleTimestamps(**lifecycle_timestamps(scan)),
        plugin_runs=plugin_runs,
    )


def _require_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    asset_service.get_for_project(db, membership, project_id=project_id, asset_id=asset_id)


def list_scan_profile_options() -> ScanProfileListResponse:
    _ensure_plugins_loaded()
    items = [
        ScanProfileSummary(**profile)
        for profile in list_scan_profiles(available_plugins=registry.list_names())
    ]
    return ScanProfileListResponse(items=items)


def list_asset_scans(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> ScanListResponse:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    scans = list_scans_for_asset(db, project_id=project_id, asset_id=asset_id)
    items = [to_scan_summary(scan) for scan in scans]
    return ScanListResponse(items=items, total=len(items))


def create_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: CreateAssetScanRequest,
) -> ScanSummary:
    asset_service.require_scannable_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    selected_plugins = _validate_create_scan(body)
    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=body.scan_type,
        selected_plugins=selected_plugins,
        created_by=membership.user_id,
    )
    record_audit_event(
        db,
        action=ScanAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="scan",
        resource_id=scan.id,
        details={
            "project_id": str(project_id),
            "asset_id": str(asset_id),
            "scan_type": body.scan_type.value,
            "plugins": selected_plugins or _profile_plugins_for_scan(scan),
        },
    )
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)


def get_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    scan = get_scan_for_asset(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    scan.plugin_runs = list_plugin_runs_for_scan(db, scan_id=scan.id)
    return to_scan_summary(scan, include_plugin_runs=True)


def run_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    asset_service.require_scannable_asset(
        db, membership, project_id=project_id, asset_id=asset_id
    )
    scan = get_scan_for_asset(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    if scan.status not in {ScanStatus.PENDING, ScanStatus.FAILED}:
        raise ValidationAppError("Scan cannot be started in its current state")

    transition_scan_status(scan, status=ScanStatus.QUEUED)
    db.add(scan)
    record_audit_event(
        db,
        action=ScanAuditAction.RUN,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="scan",
        resource_id=scan.id,
    )
    db.commit()
    db.refresh(scan)

    settings = get_settings()
    if settings.SCAN_RUN_INLINE:
        _run_queued_scan(
            db,
            scan_id=scan.id,
            project_id=project_id,
            asset_id=asset_id,
        )
        db.commit()
        db.refresh(scan)
        scan.plugin_runs = list_plugin_runs_for_scan(db, scan_id=scan.id)
    else:
        from app.jobs.scans import execute_scan
        from app.core.logging import get_correlation_id

        execute_scan.delay(
            scan_id=str(scan.id),
            project_id=str(project_id),
            asset_id=str(asset_id),
            correlation_id=get_correlation_id(),
        )

    return to_scan_summary(scan, include_plugin_runs=bool(settings.SCAN_RUN_INLINE))


def cancel_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    scan = get_scan_for_asset(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    if scan.status not in {ScanStatus.PENDING, ScanStatus.QUEUED, ScanStatus.RUNNING}:
        raise ValidationAppError("Scan cannot be cancelled in its current state")

    transition_scan_status(scan, status=ScanStatus.CANCELLED)
    db.add(scan)
    record_audit_event(
        db,
        action=ScanAuditAction.CANCEL,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="scan",
        resource_id=scan.id,
    )
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)
