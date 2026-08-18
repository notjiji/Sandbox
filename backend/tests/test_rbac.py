"""Explicit role permission tests."""

from __future__ import annotations

import uuid

import pytest

from tests.support import (
    bootstrap_org_context,
    create_pending_scan,
    create_website_asset,
    invite_and_accept_member,
)

pytestmark = pytest.mark.integration


def _forbidden(response) -> None:
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_viewer_cannot_scan_delete_asset_or_modify_organization(client, db) -> None:
    owner = bootstrap_org_context(db, client, email="rbac-viewer-owner@example.com")
    viewer = invite_and_accept_member(
        db, client, owner, email="rbac-viewer@example.com", role="viewer"
    )
    project_id = uuid.UUID(owner["project"]["id"])
    asset = create_website_asset(db, owner["membership"], project_id=project_id)
    asset_id = uuid.UUID(asset.id)
    scan = create_pending_scan(
        db, owner["membership"], project_id=project_id, asset_id=asset_id
    )
    db.commit()

    create_scan = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        json={"scan_type": "quick"},
        headers=viewer["org_headers"],
    )
    _forbidden(create_scan)

    run_scan = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/{scan.id}/run",
        headers=viewer["org_headers"],
    )
    _forbidden(run_scan)

    delete_asset = client.delete(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        headers=viewer["org_headers"],
    )
    _forbidden(delete_asset)

    patch_org = client.patch(
        "/api/v1/organizations/current",
        json={"name": "Hijacked Org"},
        headers=viewer["org_headers"],
    )
    _forbidden(patch_org)


def test_manager_cannot_perform_owner_only_actions(client, db) -> None:
    owner = bootstrap_org_context(db, client, email="rbac-manager-owner@example.com")
    manager = invite_and_accept_member(
        db, client, owner, email="rbac-manager@example.com", role="manager"
    )
    admin = invite_and_accept_member(
        db, client, owner, email="rbac-manager-admin@example.com", role="admin"
    )

    transfer = client.post(
        "/api/v1/organizations/current/transfer-ownership",
        json={"new_owner_user_id": admin["membership_id"]},
        headers=manager["org_headers"],
    )
    _forbidden(transfer)

    archive = client.patch(
        "/api/v1/organizations/current/archive",
        headers=manager["org_headers"],
    )
    _forbidden(archive)

    delete_org = client.delete(
        "/api/v1/organizations/current",
        headers=manager["org_headers"],
    )
    _forbidden(delete_org)

    invite = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "rbac-manager-invite@example.com", "role": "viewer"},
        headers=manager["org_headers"],
    )
    _forbidden(invite)


def test_analyst_can_scan(client, db) -> None:
    owner = bootstrap_org_context(db, client, email="rbac-analyst-owner@example.com")
    analyst = invite_and_accept_member(
        db,
        client,
        owner,
        email="rbac-analyst@example.com",
        role="security_analyst",
    )
    project_id = uuid.UUID(owner["project"]["id"])
    asset = create_website_asset(db, owner["membership"], project_id=project_id)
    db.commit()

    create_scan = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset.id}/scans",
        json={"scan_type": "quick"},
        headers=analyst["org_headers"],
    )
    assert create_scan.status_code == 201, create_scan.text
    scan_id = create_scan.json()["data"]["id"]

    from unittest.mock import patch

    from app.scans.enums import ScanStatus
    from app.scans.lifecycle import transition_scan_status

    def _complete(db_session, *, scan, project_id, asset_id):  # noqa: ARG001
        transition_scan_status(scan, status=ScanStatus.COMPLETED)
        db_session.add(scan)

    with patch(
        "app.scans.services.scan_executor.scan_orchestrator.execute",
        side_effect=_complete,
    ):
        with patch("app.scans.services.scan_executor.risk_engine.recalculate_after_scan"):
            run = client.post(
                f"/api/v1/projects/{project_id}/assets/{asset.id}/scans/{scan_id}/run",
                headers=analyst["org_headers"],
            )
    assert run.status_code == 200, run.text
    assert run.json()["data"]["status"] == "completed"

    patch_org = client.patch(
        "/api/v1/organizations/current",
        json={"name": "Analyst Cannot Rename"},
        headers=analyst["org_headers"],
    )
    _forbidden(patch_org)


def test_admin_can_manage_users_but_not_owner_actions(client, db) -> None:
    owner = bootstrap_org_context(db, client, email="rbac-admin-owner@example.com")
    admin = invite_and_accept_member(
        db, client, owner, email="rbac-admin@example.com", role="admin"
    )
    viewer = invite_and_accept_member(
        db, client, owner, email="rbac-admin-target@example.com", role="viewer"
    )

    invite = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "rbac-admin-new@example.com", "role": "viewer"},
        headers=admin["org_headers"],
    )
    assert invite.status_code == 201, invite.text

    promote = client.patch(
        f"/api/v1/organizations/current/members/{viewer['membership_id']}",
        json={"role": "manager"},
        headers=admin["org_headers"],
    )
    assert promote.status_code == 200, promote.text
    assert promote.json()["data"]["role"] == "manager"

    transfer = client.post(
        "/api/v1/organizations/current/transfer-ownership",
        json={"new_owner_user_id": str(admin["membership_id"])},
        headers=admin["org_headers"],
    )
    _forbidden(transfer)

    delete_org = client.delete(
        "/api/v1/organizations/current",
        headers=admin["org_headers"],
    )
    _forbidden(delete_org)


def test_owner_has_organization_level_privileges(client, db) -> None:
    owner = bootstrap_org_context(db, client, email="rbac-owner@example.com")
    admin = invite_and_accept_member(
        db, client, owner, email="rbac-owner-admin@example.com", role="admin"
    )

    renamed = client.patch(
        "/api/v1/organizations/current",
        json={"name": "Owner Renamed Org"},
        headers=owner["org_headers"],
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["data"]["name"] == "Owner Renamed Org"

    members = client.get(
        "/api/v1/organizations/current/members",
        headers=owner["org_headers"],
    )
    assert members.status_code == 200, members.text
    emails = {item["email"] for item in members.json()["data"]["items"]}
    assert "rbac-owner-admin@example.com" in emails

    from app.users.models import User

    admin_user = db.query(User).filter(User.email == admin["email"]).one()
    preview = client.post(
        "/api/v1/organizations/current/transfer-ownership",
        json={"new_owner_user_id": str(admin_user.id)},
        headers=owner["org_headers"],
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["data"]["role"] == "owner"
