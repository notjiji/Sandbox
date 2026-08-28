"""Asset unified timeline endpoint tests."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.risk.repositories.risk_repository import save_asset_risk
from app.scans.enums import ScanStatus
from app.scans.lifecycle import transition_scan_status
from app.scans.services.scan_executor import run_queued_scan
from tests.support import bootstrap_org_context, create_pending_scan, create_website_asset

pytestmark = pytest.mark.integration


def _complete_scan(db, *, scan, project_id, asset_id) -> None:  # noqa: ARG001
    transition_scan_status(scan, status=ScanStatus.COMPLETED)
    db.add(scan)


def test_asset_timeline(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-timeline@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(
        db,
        membership,
        project_id=project_id,
        name="Timeline Site",
        url="https://timeline.example.com",
    )
    asset_id = uuid.UUID(asset.id)

    scan_summary = create_pending_scan(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
    )
    scan_id = uuid.UUID(scan_summary.id)
    from app.scans.repositories.scan_repository import get_scan_for_asset

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

    # Cosmetic updates do not invalidate verification; identity fields would (see scanning docs).
    client.put(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        json={"description": "Updated after first scan"},
        headers=headers,
    )

    save_asset_risk(
        db,
        asset_id=asset_id,
        scan_id=scan_id,
        total_risk=10.0,
        score=90.0,
        grade="A",
        breakdown={"critical": 0, "high": 0, "medium": 1, "low": 0},
    )
    save_asset_risk(
        db,
        asset_id=asset_id,
        scan_id=scan_id,
        total_risk=35.0,
        score=65.0,
        grade="D",
        breakdown={"critical": 0, "high": 2, "medium": 1, "low": 0},
    )
    db.commit()

    report_response = client.post(
        f"/api/v1/projects/{project_id}/reports",
        json={"name": "Q1 Security Report"},
        headers=headers,
    )
    assert report_response.status_code == 201
    report_id = report_response.json()["data"]["id"]

    generate_response = client.post(
        f"/api/v1/projects/{project_id}/reports/{report_id}/generate",
        headers=headers,
    )
    assert generate_response.status_code == 200

    response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/timeline",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    items = payload["items"]
    assert payload["total"] >= len(items)
    assert len(items) >= 4

    messages = [item["message"] for item in items]
    categories = {item["category"] for item in items}
    actions = {item["action"] for item in items}

    assert any("Timeline Site" in message and "created" in message.lower() for message in messages)
    assert "assets" in categories
    assert "scans" in categories
    assert any("scan completed" in message.lower() for message in messages)
    assert "security" in categories
    assert any("risk score" in message.lower() for message in messages)
    assert "reports" in categories
    assert "report.generate" in actions or "report.create" in actions

    timestamps = [item["created_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)
