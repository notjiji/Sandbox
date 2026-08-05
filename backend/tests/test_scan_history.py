"""Scan history list filters and pagination tests."""

from __future__ import annotations

import uuid

import pytest

from app.risk.repositories.risk_repository import save_asset_risk
from app.scans.enums import ScanStatus, ScanType
from app.scans.repositories.scan_repository import create_scan, update_scan_status
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_scan_history_list_pagination_and_filters(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="scan-history@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    quick = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.QUICK,
        created_by=membership.user_id,
    )
    full = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.FULL,
        created_by=membership.user_id,
    )
    update_scan_status(db, quick, status=ScanStatus.QUEUED)
    update_scan_status(db, quick, status=ScanStatus.RUNNING)
    update_scan_status(db, quick, status=ScanStatus.COMPLETED)
    update_scan_status(db, full, status=ScanStatus.PENDING)
    db.commit()

    save_asset_risk(
        db,
        asset_id=asset_id,
        scan_id=quick.id,
        total_risk=12.0,
        score=88.0,
        grade="B",
        breakdown={"critical": 1, "high": 0, "medium": 1, "low": 0},
    )
    db.commit()

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans?page=1&limit=1",
        headers=headers,
    )
    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert payload["total"] >= 2
    assert payload["page"] == 1
    assert payload["limit"] == 1
    assert len(payload["items"]) == 1
    assert "metrics" in payload["items"][0]

    completed_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans?status=completed",
        headers=headers,
    )
    assert completed_response.status_code == 200
    completed_items = completed_response.json()["data"]["items"]
    assert all(item["status"] == "completed" for item in completed_items)

    quick_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans?scan_type=quick",
        headers=headers,
    )
    assert quick_response.status_code == 200
    quick_items = quick_response.json()["data"]["items"]
    assert all(item["scan_type"] == "quick" for item in quick_items)
    completed_quick = next(item for item in quick_items if item["id"] == str(quick.id))
    assert completed_quick["metrics"]["risk_score"] == 88.0
    assert completed_quick["metrics"]["critical_count"] == 1

    compare_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/compare"
        f"?scan_a={quick.id}&scan_b={full.id}",
        headers=headers,
    )
    assert compare_response.status_code == 200
    compare_payload = compare_response.json()["data"]
    assert compare_payload["scan_a"]["id"] == str(quick.id)
    assert compare_payload["scan_b"]["id"] == str(full.id)
    assert "diff" in compare_payload

    export_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/{quick.id}/export",
        headers=headers,
    )
    assert export_response.status_code == 200
    export_payload = export_response.json()["data"]
    assert export_payload["scan"]["id"] == str(quick.id)
    assert "findings" in export_payload
    assert "exported_at" in export_payload
