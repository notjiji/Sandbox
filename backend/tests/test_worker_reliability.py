"""Worker, scheduler, and background job reliability tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.reports.enums import ReportStatus, ReportType
from app.reports.repositories.report_repository import create_report, update_report
from app.scans.enums import ScanStatus, ScanType
from app.scans.repositories.scan_repository import create_scan, update_scan_status
from app.scans.services.scan_recovery import (
    fail_running_scan,
    reconcile_stale_generating_reports,
    reconcile_stale_running_scans,
)
from app.workers.job_failures import job_type_for_task_name
from tests.support import bootstrap_org_context, create_website_asset


def test_job_type_mapping() -> None:
    assert job_type_for_task_name("app.jobs.scans.execute_scan") == "scan"
    assert job_type_for_task_name("app.jobs.reports.generate_report") == "report"
    assert job_type_for_task_name("app.jobs.scans.check_due_schedules") == "scan_schedule"


def test_model_registry_resolves_audit_relationships() -> None:
    from app.audit.models import AuditLog
    from app.shared.db.models_registry import import_all_models

    import_all_models()
    assert "organization" in AuditLog.__mapper__.relationships


def test_fail_running_scan_marks_failed(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="worker-recovery@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=uuid.UUID(asset.id),
        scan_type=ScanType.QUICK,
        created_by=ctx["membership"].user_id,
    )
    update_scan_status(db, scan, status=ScanStatus.QUEUED)
    update_scan_status(db, scan, status=ScanStatus.RUNNING)
    db.commit()

    assert fail_running_scan(db, scan_id=scan.id, reason="test_failure") is True
    db.refresh(scan)
    assert scan.status == ScanStatus.FAILED


def test_reconcile_stale_running_scans(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="worker-stale-scan@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=uuid.UUID(asset.id),
        scan_type=ScanType.QUICK,
        created_by=ctx["membership"].user_id,
    )
    update_scan_status(db, scan, status=ScanStatus.QUEUED)
    update_scan_status(db, scan, status=ScanStatus.RUNNING)
    scan.running_at = datetime.now(UTC) - timedelta(hours=2)
    db.add(scan)
    db.commit()

    count = reconcile_stale_running_scans(db, stale_after_seconds=60)
    assert count == 1
    db.refresh(scan)
    assert scan.status == ScanStatus.FAILED


def test_reconcile_stale_generating_reports(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="worker-stale-report@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    report = create_report(
        db,
        project_id=project_id,
        name="Stale report",
        report_type=ReportType.TECHNICAL,
    )
    update_report(db, report, status=ReportStatus.GENERATING)
    report.updated_at = datetime.now(UTC) - timedelta(hours=2)
    db.add(report)
    db.commit()

    count = reconcile_stale_generating_reports(db, stale_after_seconds=60)
    assert count == 1
    db.refresh(report)
    assert report.status == ReportStatus.FAILED
