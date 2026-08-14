import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.assets.services.asset_service import asset_service
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember
from app.plugins.base.loader import plugin_loader
from app.plugins.base.registry import registry
from app.scans.enums import ScanStatus, ScanType
from app.scans.events import ScanAuditAction
from app.scans.lifecycle import lifecycle_timestamps, transition_scan_status
from app.scans.models import Scan
from app.scans.profiles import list_scan_profiles, resolve_profile_plugins
from app.scans.repositories.scan_plugin_repository import list_plugin_runs_for_scan
from app.findings.repositories.finding_repository import (
    count_findings_for_scans,
    list_findings_for_scan,
)
from app.risk.repositories.risk_repository import get_asset_risks_for_scans
from app.scans.repositories.scan_repository import (
    create_scan,
    get_scan_for_asset,
    list_scans_for_asset,
    list_scans_for_asset_paginated,
)
from app.scans.schemas import (
    CreateAssetScanRequest,
    ScanCompareDiff,
    ScanCompareResponse,
    ScanExportFindingSummary,
    ScanExportResponse,
    ScanLifecycleTimestamps,
    ScanListQuery,
    ScanListResponse,
    ScanMetrics,
    ScanPluginRunSummary,
    ScanProfileListResponse,
    ScanProfileSummary,
    ScanSummary,
)
from app.scans.services.scan_executor import run_queued_scan as _run_queued_scan
from app.audit.service import record_audit_event


def _ensure_plugins_loaded() -> None:
    plugin_loader.discover()


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


def _compute_duration_seconds(scan: Scan) -> float | None:
    start = scan.running_at or scan.queued_at or scan.pending_at
    end = scan.completed_at or scan.failed_at or scan.cancelled_at
    if start and end:
        return max((end - start).total_seconds(), 0.0)
    return None


def _build_metrics(
    scan: Scan,
    *,
    risk=None,
    findings_count: int = 0,
) -> ScanMetrics:
    return ScanMetrics(
        duration_seconds=_compute_duration_seconds(scan),
        risk_score=float(risk.score) if risk else None,
        grade=risk.grade if risk else None,
        critical_count=int(risk.critical_count) if risk else 0,
        findings_count=findings_count,
    )


def to_scan_summary(
    scan: Scan,
    *,
    include_plugin_runs: bool = False,
    metrics: ScanMetrics | None = None,
) -> ScanSummary:
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
        created_at=scan.created_at,
        lifecycle=ScanLifecycleTimestamps(**lifecycle_timestamps(scan)),
        plugin_runs=plugin_runs,
        metrics=metrics or ScanMetrics(),
    )


def _summaries_with_metrics(
    db: Session,
    scans: list[Scan],
    *,
    include_plugin_runs: bool = False,
) -> list[ScanSummary]:
    if not scans:
        return []

    scan_ids = [scan.id for scan in scans]
    risks = get_asset_risks_for_scans(db, scan_ids=scan_ids)
    finding_counts = count_findings_for_scans(db, scan_ids=scan_ids)
    return [
        to_scan_summary(
            scan,
            include_plugin_runs=include_plugin_runs,
            metrics=_build_metrics(
                scan,
                risk=risks.get(scan.id),
                findings_count=finding_counts.get(scan.id, 0),
            ),
        )
        for scan in scans
    ]


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
    query: ScanListQuery | None = None,
) -> ScanListResponse:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    params = query or ScanListQuery()
    scans, total = list_scans_for_asset_paginated(
        db,
        project_id=project_id,
        asset_id=asset_id,
        query=params,
    )
    items = _summaries_with_metrics(db, scans)
    return ScanListResponse(items=items, total=total, page=params.page, limit=params.limit)


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
    summaries = _summaries_with_metrics(db, [scan], include_plugin_runs=True)
    return summaries[0]


def compare_asset_scans(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_a_id: uuid.UUID,
    scan_b_id: uuid.UUID,
) -> ScanCompareResponse:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    if scan_a_id == scan_b_id:
        raise ValidationAppError("Select two different scans to compare")

    scan_a = get_scan_for_asset(
        db, project_id=project_id, asset_id=asset_id, scan_id=scan_a_id
    )
    scan_b = get_scan_for_asset(
        db, project_id=project_id, asset_id=asset_id, scan_id=scan_b_id
    )
    if not scan_a or not scan_b:
        raise NotFoundError("Scan")

    summaries = _summaries_with_metrics(db, [scan_a, scan_b])
    left, right = summaries[0], summaries[1]

    score_a = left.metrics.risk_score
    score_b = right.metrics.risk_score
    duration_a = left.metrics.duration_seconds
    duration_b = right.metrics.duration_seconds

    diff = ScanCompareDiff(
        risk_score_delta=(score_b - score_a) if score_a is not None and score_b is not None else None,
        critical_count_delta=right.metrics.critical_count - left.metrics.critical_count,
        findings_count_delta=right.metrics.findings_count - left.metrics.findings_count,
        duration_seconds_delta=(
            (duration_b - duration_a) if duration_a is not None and duration_b is not None else None
        ),
    )
    return ScanCompareResponse(scan_a=left, scan_b=right, diff=diff)


def export_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanExportResponse:
    scan = get_asset_scan(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=scan_id,
    )
    findings = list_findings_for_scan(db, project_id=project_id, scan_id=scan_id)
    return ScanExportResponse(
        scan=scan,
        findings=[
            ScanExportFindingSummary(
                id=str(finding.id),
                title=finding.title,
                severity=finding.severity.value,
                status=finding.status.value,
                risk_score=float(finding.risk_score),
                plugin=finding.plugin,
            )
            for finding in findings
        ],
        exported_at=datetime.now(UTC),
    )


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
        details={
            "project_id": str(project_id),
            "asset_id": str(asset_id),
        },
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
        details={
            "project_id": str(project_id),
            "asset_id": str(asset_id),
        },
    )
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)
