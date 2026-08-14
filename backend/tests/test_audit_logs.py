"""Audit log search and activity filter tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.audit.service import record_audit_event
from tests.support import bootstrap_org_context, create_verified_user, login_headers

pytestmark = pytest.mark.integration


def test_audit_logs_filter_scan_failures_and_actor(client, db) -> None:
    create_verified_user(
        db,
        email="amine@example.com",
        first_name="Amine",
        last_name="Haddad",
    )
    headers = login_headers(client, email="amine@example.com")
    org_response = client.post(
        "/api/v1/organizations",
        json={"name": "Audit Org"},
        headers=headers,
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["data"]["id"]
    org_headers = {**headers, "X-Organization-ID": org_id}

    user_id = None
    from app.users.models import User

    user = db.query(User).filter(User.email == "amine@example.com").one()
    user_id = user.id

    from uuid import UUID

    organization_uuid = UUID(org_id)
    record_audit_event(
        db,
        action="scan.failed",
        organization_id=organization_uuid,
        user_id=user_id,
        entity_type="scan",
        details={"asset_name": "vinca.family", "asset_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
    )
    record_audit_event(
        db,
        action="asset.create",
        organization_id=organization_uuid,
        user_id=user_id,
        entity_type="asset",
        details={"asset_name": "vinca.family"},
    )
    db.commit()

    since = (datetime.now(UTC) - timedelta(days=30)).date().isoformat()
    failed = client.get(
        "/api/v1/organizations/current/audit-logs",
        headers=org_headers,
        params={"action": "scan.failed", "date_from": since, "severity": "warning"},
    )
    assert failed.status_code == 200, failed.text
    failed_items = failed.json()["data"]["items"]
    assert len(failed_items) == 1
    assert failed_items[0]["action"] == "scan.failed"
    assert failed_items[0]["severity"] == "warning"
    assert failed_items[0]["entity_type"] == "scan"

    by_actor = client.get(
        "/api/v1/organizations/current/audit-logs",
        headers=org_headers,
        params={"actor": "Amine"},
    )
    assert by_actor.status_code == 200, by_actor.text
    actions = {item["action"] for item in by_actor.json()["data"]["items"]}
    assert "scan.failed" in actions
    assert "asset.create" in actions


def test_activity_feed_filters_and_excludes_auth(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="activity-filter@example.com")
    from uuid import UUID

    from app.users.models import User

    user = db.query(User).filter(User.email == "activity-filter@example.com").one()
    record_audit_event(
        db,
        action="scan.completed",
        organization_id=UUID(ctx["organization"]["id"]),
        user_id=user.id,
        entity_type="scan",
        details={"asset_name": "vinca.family"},
    )
    db.commit()

    response = client.get(
        "/api/v1/organizations/current/activity",
        headers=ctx["org_headers"],
        params={"action": "scan.completed"},
    )
    assert response.status_code == 200, response.text
    items = response.json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["action"] == "scan.completed"
    assert "vinca.family" in items[0]["message"]
    assert not any(item["action"].startswith("auth.") for item in items)
