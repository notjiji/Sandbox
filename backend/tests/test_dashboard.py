"""Security dashboard API tests."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from tests.support import (
    bootstrap_org_context,
    create_pending_scan,
    create_website_asset,
    invite_and_accept_member,
)

pytestmark = pytest.mark.integration

DASHBOARD_PATHS = [
    "/api/v1/organizations/current/dashboard/overview",
    "/api/v1/organizations/current/dashboard/risk-trend",
    "/api/v1/organizations/current/dashboard/findings-summary",
    "/api/v1/organizations/current/dashboard/top-assets",
    "/api/v1/organizations/current/dashboard/activity",
    "/api/v1/organizations/current/dashboard/upcoming-scans",
]


def test_dashboard_overview_returns_security_data(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-overview@example.com")

    response = client.get(DASHBOARD_PATHS[0], headers=ctx["org_headers"])
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert "score" in data
    assert "assets" in data
    assert "findings" in data
    assert "last_scan" in data
    assert data["assets"]["total"] >= 0


def test_dashboard_widget_endpoints(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-widgets@example.com")
    headers = ctx["org_headers"]
    for path in DASHBOARD_PATHS[1:]:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["success"] is True


def test_dashboard_requires_authentication(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-auth@example.com")
    response = client.get(
        DASHBOARD_PATHS[0],
        headers={"X-Organization-ID": ctx["organization"]["id"]},
    )
    assert response.status_code == 401, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_dashboard_requires_organization_header(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-org-header@example.com")
    response = client.get(DASHBOARD_PATHS[0], headers=ctx["headers"])
    assert response.status_code == 401, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_dashboard_rejects_invalid_limit(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-limit@example.com")
    response = client.get(
        "/api/v1/organizations/current/dashboard/findings-summary?limit=0",
        headers=ctx["org_headers"],
    )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_dashboard_cross_org_header_forbidden(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="dash-iso-a@example.com", org_name="Dash A")
    org_b = bootstrap_org_context(db, client, email="dash-iso-b@example.com", org_name="Dash B")

    response = client.get(
        DASHBOARD_PATHS[0],
        headers={**org_a["headers"], "X-Organization-ID": org_b["organization"]["id"]},
    )
    assert response.status_code == 403, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


def test_dashboard_data_isolated_between_organizations(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="dash-data-a@example.com", org_name="Data A")
    org_b = bootstrap_org_context(db, client, email="dash-data-b@example.com", org_name="Data B")

    create_website_asset(
        db,
        org_b["membership"],
        project_id=uuid.UUID(org_b["project"]["id"]),
        name="Org B Asset",
    )
    db.commit()

    response_a = client.get(DASHBOARD_PATHS[0], headers=org_a["org_headers"])
    response_b = client.get(DASHBOARD_PATHS[0], headers=org_b["org_headers"])
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text

    assets_a = response_a.json()["data"]["assets"]["total"]
    assets_b = response_b.json()["data"]["assets"]["total"]
    assert assets_b >= 1
    assert assets_a == 0


def test_dashboard_returns_safe_error_when_query_fails(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-fail@example.com")

    with patch(
        "app.dashboard.service.risk_service.get_dashboard_metrics",
        side_effect=RuntimeError("db exploded"),
    ):
        response = client.get(DASHBOARD_PATHS[0], headers=ctx["org_headers"])

    assert response.status_code == 503, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "DASHBOARD_UNAVAILABLE"
    assert "db exploded" not in body["error"]["message"]


def test_viewer_can_read_dashboard(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="dash-viewer-owner@example.com")
    viewer_ctx = invite_and_accept_member(
        db,
        client,
        owner_ctx,
        email="dash-viewer@example.com",
        role="viewer",
    )

    response = client.get(DASHBOARD_PATHS[0], headers=viewer_ctx["org_headers"])
    assert response.status_code == 200, response.text


def test_viewer_cannot_create_or_run_scans(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="dash-scan-owner@example.com")
    viewer_ctx = invite_and_accept_member(
        db,
        client,
        owner_ctx,
        email="dash-scan-viewer@example.com",
        role="viewer",
    )
    project_id = uuid.UUID(owner_ctx["project"]["id"])
    asset = create_website_asset(db, owner_ctx["membership"], project_id=project_id)
    asset_id = uuid.UUID(asset.id)
    scan = create_pending_scan(
        db,
        owner_ctx["membership"],
        project_id=project_id,
        asset_id=asset_id,
    )
    db.commit()

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        json={"scan_type": "quick"},
        headers=viewer_ctx["org_headers"],
    )
    assert create_response.status_code == 403, create_response.text
    assert create_response.json()["error"]["code"] == "FORBIDDEN"

    run_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/{scan.id}/run",
        headers=viewer_ctx["org_headers"],
    )
    assert run_response.status_code == 403, run_response.text
    assert run_response.json()["error"]["code"] == "FORBIDDEN"
