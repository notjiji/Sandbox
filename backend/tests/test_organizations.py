"""Organization CRUD API tests."""

from __future__ import annotations

import pytest

from tests.support import bootstrap_org_context, create_verified_user, login_headers

pytestmark = pytest.mark.integration


def test_create_list_get_update_delete_organization(client, db) -> None:
    create_verified_user(db, email="org-owner@example.com")
    headers = login_headers(client, email="org-owner@example.com")

    create_response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme Security", "description": "Primary workspace"},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["name"] == "Acme Security"
    org_id = created["id"]

    list_response = client.get("/api/v1/organizations/me", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()["data"]["items"]
    assert any(item["id"] == org_id for item in items)

    org_headers = {**headers, "X-Organization-ID": org_id}

    get_response = client.get("/api/v1/organizations/current", headers=org_headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["slug"]

    update_response = client.patch(
        "/api/v1/organizations/current",
        json={"description": "Updated description"},
        headers=org_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["description"] == "Updated description"

    delete_response = client.delete("/api/v1/organizations/current", headers=org_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True


def test_organization_routes_require_org_header(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="org-header@example.com")

    response = client.get("/api/v1/organizations/current", headers=ctx["headers"])
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_organization_settings_update(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="org-settings@example.com")

    update_response = client.patch(
        "/api/v1/organizations/current",
        json={
            "timezone": "Europe/London",
            "settings": {
                "language": "fr",
                "notifications": {"weekly_reports": False},
                "security": {"session_timeout_minutes": 240},
            },
        },
        headers=ctx["org_headers"],
    )
    assert update_response.status_code == 200, update_response.text
    data = update_response.json()["data"]
    assert data["timezone"] == "Europe/London"
    assert data["settings"]["language"] == "fr"
    assert data["settings"]["notifications"]["weekly_reports"] is False
    assert data["settings"]["security"]["session_timeout_minutes"] == 240


def test_organization_archive(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="org-archive@example.com")

    archive_response = client.patch(
        "/api/v1/organizations/current/archive",
        headers=ctx["org_headers"],
    )
    assert archive_response.status_code == 200, archive_response.text
    assert archive_response.json()["data"]["is_active"] is False


def test_organization_overview_returns_dashboard_data(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="overview@example.com")

    response = client.get(
        "/api/v1/organizations/current/overview",
        headers=ctx["org_headers"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert data["stats"]["projects"] >= 1
    assert data["stats"]["members"] >= 1
    assert "security" in data
    assert "recent_scans" in data
    assert "recent_reports" in data
    assert "recent_activity" in data
