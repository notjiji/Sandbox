"""Asset dashboard overview endpoint tests."""

from __future__ import annotations

import uuid

import pytest

from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_asset_overview(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-dashboard@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    asset = create_website_asset(
        db,
        ctx["membership"],
        project_id=project_id,
        name="Dashboard Site",
        url="https://dashboard.example.com",
    )

    response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset.id}/overview",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["asset"]["name"] == "Dashboard Site"
    assert "stats" in data
    assert "risk" in data
    assert "recent_scans" in data
    assert "top_findings" in data
    assert "recent_activity" in data
    assert "scan_trend" in data
