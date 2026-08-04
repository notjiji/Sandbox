"""Cross-organization isolation tests."""

from __future__ import annotations

import uuid

import pytest

from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_cannot_access_other_org_project(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="iso-a@example.com", org_name="Org A")
    org_b = bootstrap_org_context(db, client, email="iso-b@example.com", org_name="Org B")

    response = client.get(
        f"/api/v1/projects/{org_b['project']['id']}",
        headers=org_a["org_headers"],
    )
    assert response.status_code == 404, response.text


def test_cannot_access_other_org_asset_risk(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="risk-a@example.com", org_name="Risk Org A")
    org_b = bootstrap_org_context(db, client, email="risk-b@example.com", org_name="Risk Org B")

    asset = create_website_asset(
        db,
        org_b["membership"],
        project_id=uuid.UUID(org_b["project"]["id"]),
        name="Foreign Asset",
    )
    db.commit()

    response = client.get(
        f"/api/v1/organizations/risk/assets/{asset.id}",
        headers=org_a["org_headers"],
    )
    assert response.status_code == 404, response.text


def test_archived_organization_blocks_org_scoped_routes(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="archived-org@example.com")

    archive_response = client.patch(
        "/api/v1/organizations/current/archive",
        headers=ctx["org_headers"],
    )
    assert archive_response.status_code == 200, archive_response.text

    projects_response = client.get(
        "/api/v1/projects",
        headers=ctx["org_headers"],
    )
    assert projects_response.status_code == 404, projects_response.text


def test_cannot_revoke_other_org_invite(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="invite-a@example.com", org_name="Invite A")
    org_b = bootstrap_org_context(db, client, email="invite-b@example.com", org_name="Invite B")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "outsider@example.com", "role": "viewer"},
        headers=org_b["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text
    invite_id = invite_response.json()["data"]["invite_id"]

    revoke_response = client.delete(
        f"/api/v1/organizations/current/invites/{invite_id}",
        headers=org_a["org_headers"],
    )
    assert revoke_response.status_code == 404, revoke_response.text


def test_project_patch_rejects_is_active_toggle(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="patch-project@example.com")
    project_id = ctx["project"]["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"is_active": False},
        headers=ctx["org_headers"],
    )
    assert response.status_code == 422, response.text
    assert "archive or restore" in response.json()["error"]["message"].lower()
