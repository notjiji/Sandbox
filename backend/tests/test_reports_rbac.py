"""RBAC tests for report generation and access."""

from __future__ import annotations

import uuid

import pytest

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.scans.enums import ScanType
from app.scans.repositories.scan_repository import create_scan
from tests.support import bootstrap_org_context, create_website_asset, invite_and_accept_member

pytestmark = pytest.mark.integration


def _seed_asset_scan(db, ctx) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    project_id = uuid.UUID(ctx["project"]["id"])
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
        title="Open port",
        severity=FindingSeverity.MEDIUM,
        risk_score=20.0,
        status=FindingStatus.OPEN,
    )
    db.commit()
    return project_id, asset_id, scan.id


def test_manager_can_generate_report_viewer_cannot(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="reports-rbac-owner@example.com")
    project_id, asset_id, scan_id = _seed_asset_scan(db, owner_ctx)

    manager_ctx = invite_and_accept_member(
        db,
        client,
        owner_ctx,
        email="reports-rbac-manager@example.com",
        role="manager",
    )
    viewer_ctx = invite_and_accept_member(
        db,
        client,
        owner_ctx,
        email="reports-rbac-viewer@example.com",
        role="viewer",
    )

    manager_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports",
        json={"report_type": "executive", "scan_id": str(scan_id), "generate": True},
        headers=manager_ctx["org_headers"],
    )
    assert manager_response.status_code == 201
    report_id = manager_response.json()["data"]["id"]

    viewer_create = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports",
        json={"report_type": "technical", "generate": True},
        headers=viewer_ctx["org_headers"],
    )
    assert viewer_create.status_code == 403

    viewer_list = client.get(
        "/api/v1/organizations/current/reports",
        headers=viewer_ctx["org_headers"],
    )
    assert viewer_list.status_code == 200
    assert viewer_list.json()["data"]["total"] >= 1

    viewer_download = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports/{report_id}/download",
        headers=viewer_ctx["org_headers"],
    )
    assert viewer_download.status_code == 200

    viewer_delete = client.delete(
        f"/api/v1/projects/{project_id}/reports/{report_id}",
        headers=viewer_ctx["org_headers"],
    )
    assert viewer_delete.status_code == 403


def test_report_download_requires_authentication(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="reports-auth@example.com")
    project_id, asset_id, scan_id = _seed_asset_scan(db, ctx)
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports",
        json={"report_type": "executive", "scan_id": str(scan_id), "generate": True},
        headers=headers,
    )
    assert create_response.status_code == 201
    report_id = create_response.json()["data"]["id"]

    unauthenticated = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports/{report_id}/download",
    )
    assert unauthenticated.status_code in {401, 403}

    public_token_route = client.get("/api/v1/reports/download?token=invalid-token")
    assert public_token_route.status_code == 404


def test_organization_reports_list_includes_project_name(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="reports-org-list@example.com")
    project_id, asset_id, scan_id = _seed_asset_scan(db, ctx)

    create_response = client.post(
        f"/api/v1/projects/{project_id}/reports",
        json={
            "report_type": "technical",
            "asset_id": str(asset_id),
            "scan_id": str(scan_id),
            "generate": True,
        },
        headers=ctx["org_headers"],
    )
    assert create_response.status_code == 201

    list_response = client.get(
        "/api/v1/organizations/current/reports",
        headers=ctx["org_headers"],
    )
    assert list_response.status_code == 200
    items = list_response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["project_name"] == ctx["project"]["name"]
