"""Asset-scoped reports tests."""

from __future__ import annotations

import uuid

import pytest

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.reports.enums import ReportType
from app.reports.repositories.report_repository import create_report
from app.scans.enums import ScanType
from app.scans.repositories.scan_repository import create_scan
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_asset_reports_create_generate_download(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-reports@example.com")
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
        title="Expired SSL",
        severity=FindingSeverity.CRITICAL,
        risk_score=50.0,
        status=FindingStatus.OPEN,
    )
    db.commit()

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports",
        json={"report_type": "executive", "generate": True},
        headers=headers,
    )
    assert create_response.status_code == 201
    report = create_response.json()["data"]
    assert report["report_type"] == "executive"
    assert report["asset_id"] == str(asset_id)
    assert report["status"] == "ready"
    report_id = report["id"]

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1

    type_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports?report_type=technical",
        headers=headers,
    )
    assert type_response.status_code == 200
    assert type_response.json()["data"]["total"] == 0

    download_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports/{report_id}/download",
        headers=headers,
    )
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF")

    other_asset = create_website_asset(
        db,
        membership,
        project_id=project_id,
        name="Other",
        url="https://other.example.com",
    )
    project_report = create_report(
        db,
        project_id=project_id,
        name="Project only",
        report_type=ReportType.EXECUTIVE,
    )
    db.commit()

    isolated = client.get(
        f"/api/v1/projects/{project_id}/assets/{uuid.UUID(other_asset.id)}/reports",
        headers=headers,
    )
    assert isolated.json()["data"]["total"] == 0
    _ = project_report
