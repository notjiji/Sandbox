import pytest

from tests.support import bootstrap_org_context

pytestmark = pytest.mark.integration


def test_dashboard_overview_returns_security_data(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="dash-overview@example.com")

    response = client.get(
        "/api/v1/organizations/current/dashboard/overview",
        headers=ctx["org_headers"],
    )
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
    paths = [
        "/api/v1/organizations/current/dashboard/risk-trend",
        "/api/v1/organizations/current/dashboard/findings-summary",
        "/api/v1/organizations/current/dashboard/top-assets",
        "/api/v1/organizations/current/dashboard/activity",
        "/api/v1/organizations/current/dashboard/upcoming-scans",
    ]
    for path in paths:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["success"] is True
