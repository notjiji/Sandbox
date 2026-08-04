"""Scan orchestration tests."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.scans.enums import ScanStatus
from app.scans.lifecycle import transition_scan_status
from app.scans.repositories.scan_repository import get_scan_for_asset
from app.scans.services.scan_executor import run_queued_scan
from tests.support import bootstrap_org_context, create_pending_scan, create_website_asset

pytestmark = pytest.mark.integration


def _complete_scan(db, *, scan, project_id, asset_id) -> None:  # noqa: ARG001
    from app.scans.lifecycle import transition_scan_status

    transition_scan_status(scan, status=ScanStatus.COMPLETED)
    db.add(scan)


def test_create_and_run_scan_via_api(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="scan-user@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        json={"scan_type": "quick"},
        headers=headers,
    )
    assert create_response.status_code == 201
    scan_id = create_response.json()["data"]["id"]

    with patch(
        "app.scans.services.scan_executor.scan_orchestrator.execute",
        side_effect=_complete_scan,
    ):
        with patch("app.scans.services.scan_executor.risk_engine.recalculate_after_scan"):
            run_response = client.post(
                f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/{scan_id}/run",
                headers=headers,
            )

    assert run_response.status_code == 200
    assert run_response.json()["data"]["status"] == "completed"


def _queue_scan(db, *, project_id: uuid.UUID, asset_id: uuid.UUID, scan_id: uuid.UUID) -> None:
    scan = get_scan_for_asset(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=scan_id,
    )
    assert scan is not None
    transition_scan_status(scan, status=ScanStatus.QUEUED)
    db.add(scan)
    db.commit()


def test_scan_executor_completes_with_mocked_orchestrator(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="executor@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    asset_id = uuid.UUID(asset.id)
    scan_summary = create_pending_scan(
        db,
        ctx["membership"],
        project_id=project_id,
        asset_id=asset_id,
    )
    scan_id = uuid.UUID(scan_summary.id)
    _queue_scan(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)

    with patch(
        "app.scans.services.scan_executor.scan_orchestrator.execute",
        side_effect=_complete_scan,
    ):
        with patch("app.scans.services.scan_executor.risk_engine.recalculate_after_scan"):
            run_queued_scan(
                db,
                scan_id=scan_id,
                project_id=project_id,
                asset_id=asset_id,
            )
            db.commit()

    stored = get_scan_for_asset(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=scan_id,
    )
    assert stored is not None
    assert stored.status == ScanStatus.COMPLETED


def test_scan_executor_marks_failed_on_orchestrator_error(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="executor-fail@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    asset_id = uuid.UUID(asset.id)
    scan_summary = create_pending_scan(
        db,
        ctx["membership"],
        project_id=project_id,
        asset_id=asset_id,
    )
    scan_id = uuid.UUID(scan_summary.id)
    _queue_scan(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)

    with patch(
        "app.scans.services.scan_executor.scan_orchestrator.execute",
        side_effect=RuntimeError("plugin pipeline failed"),
    ):
        with patch("app.scans.services.scan_executor.risk_engine.recalculate_after_scan"):
            run_queued_scan(
                db,
                scan_id=scan_id,
                project_id=project_id,
                asset_id=asset_id,
            )
            db.commit()

    stored = get_scan_for_asset(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=scan_id,
    )
    assert stored is not None
    assert stored.status == ScanStatus.FAILED
