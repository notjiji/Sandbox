"""Asset notes field tests."""

from __future__ import annotations

import uuid

import pytest

from tests.support import bootstrap_org_context

pytestmark = pytest.mark.integration


def test_asset_notes_create_update_and_search(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-notes@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Notes Site",
            "type": "website",
            "status": "active",
            "metadata": {"url": "https://notes.example.com"},
            "tags": ["production", "website"],
            "notes": "Primary customer portal — page on-call before changes.",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    asset_id = created["id"]
    assert created["notes"] == "Primary customer portal — page on-call before changes."
    assert created["tags"] == ["production", "website"]

    update_response = client.put(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        json={"notes": "Updated runbook: rotate TLS certs quarterly."},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["notes"] == "Updated runbook: rotate TLS certs quarterly."

    search_response = client.get(
        f"/api/v1/projects/{project_id}/assets?search=runbook",
        headers=headers,
    )
    assert search_response.status_code == 200
    assert search_response.json()["data"]["total"] == 1
    assert search_response.json()["data"]["items"][0]["id"] == asset_id
