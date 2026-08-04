"""Additional member and organization lifecycle tests."""

from __future__ import annotations

import pytest

from tests.support import TEST_PASSWORD, bootstrap_org_context, create_verified_user, login_headers

pytestmark = pytest.mark.integration


def test_remove_member_soft_deletes_membership(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="owner-remove@example.com")
    create_verified_user(db, email="member-remove@example.com")

    client.post(
        "/api/v1/organizations/current/members",
        json={"email": "member-remove@example.com", "role": "viewer"},
        headers=owner_ctx["org_headers"],
    )
    member_headers = login_headers(client, email="member-remove@example.com")
    accept_response = client.post(
        "/api/v1/organizations/current/members/accept",
        headers={**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]},
    )
    membership_id = accept_response.json()["data"]["membership_id"]

    remove_response = client.delete(
        f"/api/v1/organizations/current/members/{membership_id}",
        headers=owner_ctx["org_headers"],
    )
    assert remove_response.status_code == 200, remove_response.text

    list_response = client.get(
        "/api/v1/organizations/current/members",
        headers=owner_ctx["org_headers"],
    )
    assert list_response.status_code == 200, list_response.text
    emails = [item["email"] for item in list_response.json()["data"]["items"]]
    assert "member-remove@example.com" not in emails

    blocked_response = client.get(
        "/api/v1/organizations/current",
        headers={**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]},
    )
    assert blocked_response.status_code == 403, blocked_response.text


def test_cannot_remove_self_or_owner(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="owner-guard@example.com")
    owner_membership_id = owner_ctx["membership"].id

    self_remove = client.delete(
        f"/api/v1/organizations/current/members/{owner_membership_id}",
        headers=owner_ctx["org_headers"],
    )
    assert self_remove.status_code == 403, self_remove.text


def test_transfer_ownership(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="owner-transfer@example.com")
    create_verified_user(db, email="new-owner@example.com")

    client.post(
        "/api/v1/organizations/current/members",
        json={"email": "new-owner@example.com", "role": "admin"},
        headers=owner_ctx["org_headers"],
    )
    member_headers = login_headers(client, email="new-owner@example.com")
    accept_response = client.post(
        "/api/v1/organizations/current/members/accept",
        headers={**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]},
    )
    new_owner_user_id = accept_response.json()["data"]["user_id"]

    transfer_response = client.post(
        "/api/v1/organizations/current/transfer-ownership",
        json={"new_owner_user_id": new_owner_user_id},
        headers=owner_ctx["org_headers"],
    )
    assert transfer_response.status_code == 200, transfer_response.text
    assert transfer_response.json()["data"]["role"] == "owner"

    me_response = client.get("/api/v1/organizations/me", headers=owner_ctx["headers"])
    org_item = next(
        item for item in me_response.json()["data"]["items"] if item["id"] == owner_ctx["organization"]["id"]
    )
    assert org_item["role"] == "admin"


def test_resend_and_list_pending_invites(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-resend@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "resend-target@example.com", "role": "viewer"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text
    invite_id = invite_response.json()["data"]["invite_id"]

    list_response = client.get(
        "/api/v1/organizations/current/invites",
        headers=ctx["org_headers"],
    )
    assert list_response.status_code == 200, list_response.text
    invite_ids = [item["invite_id"] for item in list_response.json()["data"]["items"]]
    assert invite_id in invite_ids

    resend_response = client.post(
        f"/api/v1/organizations/current/invites/{invite_id}/resend?send_email=false",
        headers=ctx["org_headers"],
    )
    assert resend_response.status_code == 200, resend_response.text
    assert resend_response.json()["data"]["invite_link"]


def test_organization_restore_after_archive(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-restore@example.com")
    org_id = ctx["organization"]["id"]

    archive_response = client.patch(
        "/api/v1/organizations/current/archive",
        headers=ctx["org_headers"],
    )
    assert archive_response.status_code == 200, archive_response.text
    assert archive_response.json()["data"]["is_active"] is False

    blocked_response = client.get(
        "/api/v1/organizations/current/overview",
        headers=ctx["org_headers"],
    )
    assert blocked_response.status_code == 404, blocked_response.text

    restore_response = client.patch(
        f"/api/v1/organizations/{org_id}/restore",
        headers=ctx["headers"],
    )
    assert restore_response.status_code == 200, restore_response.text
    assert restore_response.json()["data"]["is_active"] is True

    overview_response = client.get(
        "/api/v1/organizations/current/overview",
        headers=ctx["org_headers"],
    )
    assert overview_response.status_code == 200, overview_response.text


def test_organization_delete_is_distinct_from_archive(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-delete@example.com")
    org_id = ctx["organization"]["id"]

    archive_response = client.patch(
        "/api/v1/organizations/current/archive",
        headers=ctx["org_headers"],
    )
    assert archive_response.status_code == 200, archive_response.text

    blocked_delete = client.delete(
        "/api/v1/organizations/current",
        headers=ctx["org_headers"],
    )
    assert blocked_delete.status_code == 404, blocked_delete.text

    restore_response = client.patch(
        f"/api/v1/organizations/{org_id}/restore",
        headers=ctx["headers"],
    )
    assert restore_response.status_code == 200, restore_response.text

    delete_response = client.delete(
        "/api/v1/organizations/current",
        headers=ctx["org_headers"],
    )
    assert delete_response.status_code == 200, delete_response.text

    list_response = client.get("/api/v1/organizations/me", headers=ctx["headers"])
    assert list_response.status_code == 200, list_response.text
    assert not any(item["id"] == org_id for item in list_response.json()["data"]["items"])
