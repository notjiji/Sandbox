"""Asset API card-field enrichment tests."""

from __future__ import annotations

import uuid

import pytest

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.risk.repositories.risk_repository import save_asset_risk
from app.scans.enums import ScanStatus, ScanType
from app.scans.repositories.scan_repository import create_scan, update_scan_status
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def _complete_scan(db, scan) -> None:
    update_scan_status(db, scan, status=ScanStatus.QUEUED)
    update_scan_status(db, scan, status=ScanStatus.RUNNING)
    update_scan_status(db, scan, status=ScanStatus.COMPLETED)


def _assert_card_fields(payload: dict) -> None:
    for key in (
        "id",
        "name",
        "type",
        "security_score",
        "critical_findings",
        "last_scan",
        "next_scan",
        "health_status",
    ):
        assert key in payload, f"missing card field: {key}"


def test_asset_endpoints_include_card_fields(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-card-fields@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(
        db,
        membership,
        project_id=project_id,
        name="Card Site",
        url="https://card.example.com",
    )
    asset_id = uuid.UUID(asset.id)

    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.QUICK,
        created_by=membership.user_id,
    )
    _complete_scan(db, scan)
    db.commit()

    save_asset_risk(
        db,
        asset_id=asset_id,
        scan_id=scan.id,
        total_risk=18.0,
        score=82.4,
        grade="B",
        breakdown={"critical": 0, "high": 0, "medium": 1, "low": 0},
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan.id,
        asset_id=asset_id,
        title="Exposed admin panel",
        severity=FindingSeverity.CRITICAL,
        risk_score=25.0,
        status=FindingStatus.OPEN,
    )
    db.commit()

    schedules_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scan-schedules",
        headers=headers,
    )
    assert schedules_response.status_code == 200

    enable_response = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scan-schedules/quick_daily",
        json={"enabled": True},
        headers=headers,
    )
    assert enable_response.status_code == 200
    next_run_at = enable_response.json()["data"]["next_run_at"]
    assert next_run_at is not None

    get_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    detail = get_response.json()["data"]
    _assert_card_fields(detail)
    assert detail["security_score"] == 82
    assert detail["critical_findings"] == 1
    assert detail["last_scan"] is not None
    assert detail["next_scan"] is not None
    assert detail["health_status"] == "Critical"
    assert detail["current_risk_score"] == 82.4
    assert detail["critical_findings_count"] == 1

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed = list_response.json()["data"]["items"][0]
    _assert_card_fields(listed)
    assert listed["security_score"] == 82
    assert listed["health_status"] == "Critical"


def test_unscanned_asset_health_status(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-card-unscanned@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Fresh Site",
            "type": "website",
            "status": "active",
            "metadata": {"url": "https://fresh.example.com"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    _assert_card_fields(created)
    assert created["security_score"] is None
    assert created["critical_findings"] == 0
    assert created["last_scan"] is None
    assert created["next_scan"] is None
    assert created["health_status"] == "Unscanned"
