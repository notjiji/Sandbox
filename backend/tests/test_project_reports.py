"""Project-scoped reports tests."""

from __future__ import annotations

import uuid

import pytest

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.scans.enums import ScanType
from app.scans.repositories.scan_repository import create_scan
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_project_reports_create_preview_list(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="project-reports@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.QUICK,
        created_by=membership.user_id,
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan.id,
        asset_id=asset_id,
        title="Missing CSP",
        severity=FindingSeverity.HIGH,
        risk_score=30.0,
        status=FindingStatus.OPEN,
    )
    db.commit()

    create_response = client.post(
        f"/api/v1/projects/{project_id}/reports",
        json={
            "report_type": "technical",
            "asset_id": str(asset_id),
            "scan_id": str(scan.id),
            "generate": True,
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    report = create_response.json()["data"]
    assert report["status"] == "ready"
    assert report["created_by_name"]
    report_id = report["id"]

    list_response = client.get(
        f"/api/v1/projects/{project_id}/reports",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed = list_response.json()["data"]["items"]
    assert len(listed) == 1
    assert listed[0]["created_by_name"]

    preview_response = client.get(
        f"/api/v1/projects/{project_id}/reports/{report_id}/preview",
        headers=headers,
    )
    assert preview_response.status_code == 200
    assert "text/html" in preview_response.headers["content-type"]
    assert "Missing CSP" in preview_response.text or "Security" in preview_response.text
