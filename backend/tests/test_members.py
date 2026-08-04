"""Member management API tests."""

from __future__ import annotations

import pytest

from tests.support import bootstrap_org_context, create_verified_user, login_headers

pytestmark = pytest.mark.integration


def test_member_list_supports_search_and_status_filter(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="members-list@example.com")

    response = client.get(
        "/api/v1/organizations/current/members",
        headers=ctx["org_headers"],
        params={"status": "active", "sort": "email", "order": "asc"},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["total"] >= 1
    assert body["page"] == 1
    assert all(item["status"] == "active" for item in body["items"])


def test_suspend_and_reactivate_member(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="owner-suspend@example.com")
    create_verified_user(db, email="member-suspend@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "member-suspend@example.com", "role": "viewer"},
        headers=owner_ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    member_headers = login_headers(client, email="member-suspend@example.com")
    accept_response = client.post(
        "/api/v1/organizations/current/members/accept",
        headers={**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]},
    )
    assert accept_response.status_code == 200, accept_response.text
    membership_id = accept_response.json()["data"]["membership_id"]

    suspend_response = client.patch(
        f"/api/v1/organizations/current/members/{membership_id}",
        json={"status": "suspended"},
        headers=owner_ctx["org_headers"],
    )
    assert suspend_response.status_code == 200, suspend_response.text
    assert suspend_response.json()["data"]["status"] == "suspended"

    reactivate_response = client.patch(
        f"/api/v1/organizations/current/members/{membership_id}",
        json={"status": "active"},
        headers=owner_ctx["org_headers"],
    )
    assert reactivate_response.status_code == 200, reactivate_response.text
    assert reactivate_response.json()["data"]["status"] == "active"


def test_update_member_role(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="owner-role@example.com")
    create_verified_user(db, email="member-role@example.com")

    client.post(
        "/api/v1/organizations/current/members",
        json={"email": "member-role@example.com", "role": "viewer"},
        headers=owner_ctx["org_headers"],
    )
    member_headers = login_headers(client, email="member-role@example.com")
    accept_response = client.post(
        "/api/v1/organizations/current/members/accept",
        headers={**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]},
    )
    membership_id = accept_response.json()["data"]["membership_id"]

    update_response = client.patch(
        f"/api/v1/organizations/current/members/{membership_id}",
        json={"role": "manager"},
        headers=owner_ctx["org_headers"],
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["data"]["role"] == "manager"
