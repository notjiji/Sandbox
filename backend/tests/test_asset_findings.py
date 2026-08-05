"""Asset-scoped findings list tests."""

from __future__ import annotations

import uuid

import pytest

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.scans.enums import ScanType
from app.scans.repositories.scan_repository import create_scan
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_asset_findings_list_filters(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-findings@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    other_asset = create_website_asset(
        db,
        membership,
        project_id=project_id,
        name="Other Site",
        url="https://other.example.com",
    )

    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.QUICK,
        created_by=membership.user_id,
    )
    other_scan = create_scan(
        db,
        project_id=project_id,
        asset_id=uuid.UUID(other_asset.id),
        scan_type=ScanType.QUICK,
        created_by=membership.user_id,
    )
    db.commit()

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
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan.id,
        asset_id=asset_id,
        title="Missing CSP",
        severity=FindingSeverity.MEDIUM,
        risk_score=15.0,
        status=FindingStatus.RESOLVED,
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan.id,
        asset_id=asset_id,
        title="Server Header",
        severity=FindingSeverity.LOW,
        risk_score=5.0,
        status=FindingStatus.FALSE_POSITIVE,
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=other_scan.id,
        asset_id=uuid.UUID(other_asset.id),
        title="Other asset issue",
        severity=FindingSeverity.HIGH,
        risk_score=30.0,
        status=FindingStatus.OPEN,
    )
    db.commit()

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/findings",
        headers=headers,
    )
    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert payload["total"] == 3
    assert len(payload["items"]) == 3
    titles = {item["title"] for item in payload["items"]}
    assert "Expired SSL" in titles
    assert "Other asset issue" not in titles

    open_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/findings?status_group=open",
        headers=headers,
    )
    assert open_response.status_code == 200
    open_items = open_response.json()["data"]["items"]
    assert len(open_items) == 1
    assert open_items[0]["title"] == "Expired SSL"

    resolved_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/findings?status_group=resolved",
        headers=headers,
    )
    assert resolved_response.status_code == 200
    assert resolved_response.json()["data"]["items"][0]["title"] == "Missing CSP"

    ignored_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/findings?status_group=ignored",
        headers=headers,
    )
    assert ignored_response.status_code == 200
    assert ignored_response.json()["data"]["items"][0]["title"] == "Server Header"

    search_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/findings?search=ssl",
        headers=headers,
    )
    assert search_response.status_code == 200
    assert search_response.json()["data"]["total"] == 1

    severity_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/findings?severity=critical",
        headers=headers,
    )
    assert severity_response.status_code == 200
    assert severity_response.json()["data"]["total"] == 1
