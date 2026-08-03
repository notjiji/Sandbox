"""Scan plugin run persistence — per-plugin execution status for a scan."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.scans.enums import PluginRunStatus
from app.scans.models import ScanPluginRun


def create_plugin_run(
    db: Session,
    *,
    scan_id: uuid.UUID,
    asset_id: uuid.UUID,
    plugin_name: str,
    status: PluginRunStatus = PluginRunStatus.PENDING,
) -> ScanPluginRun:
    plugin_run = ScanPluginRun(
        scan_id=scan_id,
        asset_id=asset_id,
        plugin_name=plugin_name,
        status=status,
        started_at=datetime.now(UTC) if status == PluginRunStatus.RUNNING else None,
    )
    db.add(plugin_run)
    db.flush()
    return plugin_run


def complete_plugin_run(
    db: Session,
    plugin_run: ScanPluginRun,
    *,
    status: PluginRunStatus,
    findings_count: int = 0,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> ScanPluginRun:
    plugin_run.status = status
    plugin_run.findings_count = findings_count
    plugin_run.error_message = error_message
    plugin_run.metadata_json = metadata
    plugin_run.completed_at = datetime.now(UTC)
    if plugin_run.started_at is None:
        plugin_run.started_at = plugin_run.completed_at
    db.add(plugin_run)
    db.flush()
    return plugin_run


def list_plugin_runs_for_scan(db: Session, *, scan_id: uuid.UUID) -> list[ScanPluginRun]:
    return (
        db.query(ScanPluginRun)
        .filter(ScanPluginRun.scan_id == scan_id)
        .order_by(ScanPluginRun.created_at.asc())
        .all()
    )
