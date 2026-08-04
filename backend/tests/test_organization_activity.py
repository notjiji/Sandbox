"""Organization activity feed tests."""

from __future__ import annotations

import pytest

from tests.support import TEST_PASSWORD, bootstrap_org_context, create_verified_user, login_headers

pytestmark = pytest.mark.integration


def test_organization_activity_returns_human_friendly_events(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="activity-owner@example.com")
    create_verified_user(db, email="activity-member@example.com")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "activity-member@example.com", "role": "viewer"},
        headers=ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    response = client.get(
        "/api/v1/organizations/current/activity",
        headers=ctx["org_headers"],
        params={"page": 1, "limit": 10},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["total"] >= 1
    assert body["page"] == 1
    assert len(body["items"]) >= 1

    invite_event = next(
        (item for item in body["items"] if item["action"] == "org.member_invite"),
        None,
    )
    assert invite_event is not None
    assert "invited" in invite_event["message"].lower()
    assert invite_event["category"] == "members"
    assert invite_event["actor"]["name"]


def test_organization_activity_excludes_auth_events(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="activity-auth@example.com")

    response = client.get(
        "/api/v1/organizations/current/activity",
        headers=ctx["org_headers"],
    )
    assert response.status_code == 200, response.text
    actions = [item["action"] for item in response.json()["data"]["items"]]
    assert not any(action.startswith("auth.") for action in actions)


def test_organization_overview_activity_is_enriched(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="overview-activity@example.com")

    response = client.get(
        "/api/v1/organizations/current/overview",
        headers=ctx["org_headers"],
    )
    assert response.status_code == 200, response.text
    activity = response.json()["data"]["recent_activity"]
    assert isinstance(activity, list)
    if activity:
        assert "message" in activity[0]
        assert "category" in activity[0]
