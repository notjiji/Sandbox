"""Project CRUD and overview API tests."""

from __future__ import annotations

import pytest

from tests.support import bootstrap_org_context

pytestmark = pytest.mark.integration


def test_project_crud_archive_restore(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="project-crud@example.com")

    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Security Program", "description": "Primary scope"},
        headers=ctx["org_headers"],
    )
    assert create_response.status_code == 201, create_response.text
    project = create_response.json()["data"]
    project_id = project["id"]

    update_response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"description": "Updated scope"},
        headers=ctx["org_headers"],
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["description"] == "Updated scope"

    overview_response = client.get(
        f"/api/v1/projects/{project_id}/overview",
        headers=ctx["org_headers"],
    )
    assert overview_response.status_code == 200
    overview = overview_response.json()["data"]
    assert overview["project"]["id"] == project_id
    assert "stats" in overview
    assert "security" in overview

    archive_response = client.patch(
        f"/api/v1/projects/{project_id}/archive",
        headers=ctx["org_headers"],
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["is_active"] is False

    restore_response = client.patch(
        f"/api/v1/projects/{project_id}/restore",
        headers=ctx["org_headers"],
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["is_active"] is True

    delete_response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers=ctx["org_headers"],
    )
    assert delete_response.status_code == 200


def test_project_activity_endpoint(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="project-activity@example.com")
    project_id = ctx["project"]["id"]

    response = client.get(
        f"/api/v1/projects/{project_id}/activity",
        headers=ctx["org_headers"],
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert "items" in body
    assert body["total"] >= 1
