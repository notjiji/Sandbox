"""Per-asset scan schedule tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.scans.enums import SchedulePreset
from app.scans.repositories.schedule_repository import get_schedule_for_asset
from app.scans.services import schedule_service
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_asset_scan_schedules_list_defaults_and_toggle(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="scan-schedules@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scan-schedules",
        headers=headers,
    )
    assert list_response.status_code == 200
    items = list_response.json()["data"]["items"]
    assert len(items) == 4
    assert items[0]["preset"] == "quick_daily"
    assert items[0]["label"] == "Quick Scan"
    assert items[0]["cadence"] == "Daily"
    assert items[0]["enabled"] is False
    assert items[1]["preset"] == "full_sunday"
    assert items[2]["preset"] == "ssl_12h"
    assert items[3]["preset"] == "dns_weekly"

    enable_response = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scan-schedules/quick_daily",
        json={"enabled": True},
        headers=headers,
    )
    assert enable_response.status_code == 200
    enabled = enable_response.json()["data"]
    assert enabled["enabled"] is True
    assert enabled["next_run_at"] is not None

    disable_response = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scan-schedules/quick_daily",
        json={"enabled": False},
        headers=headers,
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["enabled"] is False


def test_fire_due_schedules_creates_scan(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="scan-schedules-fire@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id)
    asset_id = uuid.UUID(asset.id)

    client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scan-schedules",
        headers=headers,
    )

    schedule = get_schedule_for_asset(
        db,
        project_id=project_id,
        asset_id=asset_id,
        preset=SchedulePreset.SSL_12H,
    )
    assert schedule is not None
    schedule.enabled = True
    schedule.next_run_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    fired = schedule_service.fire_due_schedules(db)
    assert fired == 1

    db.refresh(schedule)
    assert schedule.last_run_at is not None
    assert schedule.last_scan_id is not None
    assert schedule.next_run_at is not None
    assert schedule.next_run_at > schedule.last_run_at

    scans_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        headers=headers,
    )
    assert scans_response.status_code == 200
    assert scans_response.json()["data"]["total"] >= 1
