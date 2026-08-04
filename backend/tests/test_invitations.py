"""Organization invitation lifecycle tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import hash_token
from app.organizations.invites import OrganizationInvite
from app.organizations.repositories.invite_repository import get_invite_by_token_hash
from tests.support import TEST_PASSWORD, bootstrap_org_context, create_verified_user, login_headers

pytestmark = pytest.mark.integration

KNOWN_INVITE_TOKEN = "test-invite-token-for-lifecycle-tests"


@pytest.fixture
def fixed_invite_token(monkeypatch) -> str:
    monkeypatch.setattr(
        "app.members.services.invite_service.generate_opaque_token",
        lambda: KNOWN_INVITE_TOKEN,
    )
    return KNOWN_INVITE_TOKEN


def _invite_token_from_db(db, token: str = KNOWN_INVITE_TOKEN) -> OrganizationInvite:
    invite = get_invite_by_token_hash(db, token_hash=hash_token(token))
    assert invite is not None
    return invite


def test_invite_preview_pending(client, db, fixed_invite_token) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-preview@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "pending-preview@example.com", "role": "viewer"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    preview_response = client.get(f"/api/v1/organizations/invites/{fixed_invite_token}")
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()["data"]
    assert preview["status"] == "pending"
    assert preview["email"] == "pending-preview@example.com"
    assert preview["organization_name"] == ctx["organization"]["name"]


def test_accept_invite_by_token(client, db, fixed_invite_token) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-accept@example.com")
    create_verified_user(db, email="accept-token@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "accept-token@example.com", "role": "manager"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    member_headers = login_headers(client, email="accept-token@example.com")
    accept_response = client.post(
        f"/api/v1/organizations/invites/{fixed_invite_token}/accept",
        headers=member_headers,
    )
    assert accept_response.status_code == 200, accept_response.text
    body = accept_response.json()["data"]
    assert body["id"] == ctx["organization"]["id"]
    assert body["role"] == "manager"

    preview_response = client.get(f"/api/v1/organizations/invites/{fixed_invite_token}")
    assert preview_response.status_code == 200, preview_response.text
    assert preview_response.json()["data"]["status"] == "accepted"


def test_revoke_invite(client, db, fixed_invite_token) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-revoke@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "revoked-user@example.com", "role": "viewer"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text
    invite_id = invite_response.json()["data"]["invite_id"]

    revoke_response = client.delete(
        f"/api/v1/organizations/current/invites/{invite_id}",
        headers=ctx["org_headers"],
    )
    assert revoke_response.status_code == 200, revoke_response.text

    preview_response = client.get(f"/api/v1/organizations/invites/{fixed_invite_token}")
    assert preview_response.status_code == 200, preview_response.text
    assert preview_response.json()["data"]["status"] == "revoked"


def test_expired_invite_is_marked_and_rejected(client, db, fixed_invite_token) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-expired@example.com")
    create_verified_user(db, email="expired-user@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "expired-user@example.com", "role": "viewer"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    invite = _invite_token_from_db(db)
    invite.expires_at = datetime.now(UTC) - timedelta(days=1)
    db.commit()

    preview_response = client.get(f"/api/v1/organizations/invites/{fixed_invite_token}")
    assert preview_response.status_code == 200, preview_response.text
    assert preview_response.json()["data"]["status"] == "expired"

    member_headers = login_headers(client, email="expired-user@example.com")
    accept_response = client.post(
        f"/api/v1/organizations/invites/{fixed_invite_token}/accept",
        headers=member_headers,
    )
    assert accept_response.status_code == 410, accept_response.text
    assert accept_response.json()["error"]["code"] == "INVITE_EXPIRED"


def test_register_with_invite_token(client, db, fixed_invite_token) -> None:
    ctx = bootstrap_org_context(db, client, email="owner-register@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "register-invite@example.com", "role": "security_analyst"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Invited",
            "last_name": "User",
            "email": "register-invite@example.com",
            "password": TEST_PASSWORD,
            "invite_token": fixed_invite_token,
        },
    )
    assert register_response.status_code == 201, register_response.text
    body = register_response.json()["data"]
    assert body["organization"]["id"] == ctx["organization"]["id"]
    assert body["organization"]["role"] == "security_analyst"

    preview_response = client.get(f"/api/v1/organizations/invites/{fixed_invite_token}")
    assert preview_response.status_code == 200, preview_response.text
    assert preview_response.json()["data"]["status"] == "accepted"
