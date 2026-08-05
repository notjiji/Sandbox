"""Asset risk history endpoint tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.risk.models import AssetRisk
from app.risk.repositories.risk_repository import save_asset_risk
from app.scans.enums import ScanStatus, ScanType
from app.scans.repositories.scan_repository import create_scan, update_scan_status
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def _complete_scan(db, scan) -> None:
    update_scan_status(db, scan, status=ScanStatus.QUEUED)
    update_scan_status(db, scan, status=ScanStatus.RUNNING)
    update_scan_status(db, scan, status=ScanStatus.COMPLETED)


def test_asset_risk_history_trend_and_explanations(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="risk-history@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    scan_a = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.QUICK,
        created_by=membership.user_id,
    )
    _complete_scan(db, scan_a)
    db.commit()

    save_asset_risk(
        db,
        asset_id=asset_id,
        scan_id=scan_a.id,
        total_risk=18.0,
        score=82.0,
        grade="B",
        breakdown={"critical": 0, "high": 0, "medium": 1, "low": 0},
    )
    first_risk = db.query(AssetRisk).filter(AssetRisk.asset_id == asset_id).one()
    first_risk.calculated_at = datetime.now(UTC) - timedelta(days=2)
    db.add(first_risk)

    missing_csp = create_finding(
        db,
        project_id=project_id,
        scan_id=scan_a.id,
        asset_id=asset_id,
        title="Missing CSP",
        severity=FindingSeverity.HIGH,
        risk_score=15.0,
        status=FindingStatus.OPEN,
    )
    missing_csp.created_at = datetime.now(UTC) - timedelta(days=1, hours=12)
    db.add(missing_csp)
    db.commit()

    scan_b = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.FULL,
        created_by=membership.user_id,
    )
    _complete_scan(db, scan_b)
    db.commit()

    save_asset_risk(
        db,
        asset_id=asset_id,
        scan_id=scan_b.id,
        total_risk=38.0,
        score=62.0,
        grade="D",
        breakdown={"critical": 0, "high": 2, "medium": 1, "low": 0},
    )
    second_risk = (
        db.query(AssetRisk)
        .filter(AssetRisk.asset_id == asset_id)
        .order_by(AssetRisk.calculated_at.desc())
        .first()
    )
    assert second_risk is not None
    second_risk.calculated_at = datetime.now(UTC) - timedelta(days=1)
    db.add(second_risk)

    ssh_finding = create_finding(
        db,
        project_id=project_id,
        scan_id=scan_b.id,
        asset_id=asset_id,
        title="SSH exposed",
        severity=FindingSeverity.HIGH,
        risk_score=5.0,
        status=FindingStatus.OPEN,
    )
    ssh_finding.created_at = datetime.now(UTC) - timedelta(days=1, hours=12)
    db.add(ssh_finding)
    db.commit()

    response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/risk-history",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert len(payload["trend"]) >= 2
    assert payload["latest_change"] is not None
    assert payload["latest_change"]["score_delta"] == pytest.approx(-20.0)
    titles = [item["title"] for item in payload["latest_change"]["explanations"]]
    assert any("SSH exposed" in title for title in titles)
    assert any("Missing CSP" in title for title in titles)
