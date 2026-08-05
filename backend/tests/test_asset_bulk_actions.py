"""Asset bulk action tests."""

from __future__ import annotations

import uuid

import pytest

from app.assets.enums import AssetStatus
from app.assets.repositories.asset_repository import get_asset_by_id
from app.assets.schemas import CreateAssetRequest
from app.assets.services import create_project_asset
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_bulk_archive_assign_tags_change_owner(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="bulk-assets@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    first = create_website_asset(db, membership, project_id=project_id, name="Bulk One")
    second = create_project_asset(
        db,
        membership,
        project_id=project_id,
        body=CreateAssetRequest(
            name="Bulk Two",
            metadata={"url": "https://bulk-two.example.com"},
            tags=["legacy"],
        ),
    )
    db.commit()

    tag_response = client.post(
        f"/api/v1/projects/{project_id}/assets/bulk",
        json={
            "asset_ids": [first.id, second.id],
            "action": "assign_tags",
            "tags": ["production", "customer"],
            "tag_mode": "add",
        },
        headers=headers,
    )
    assert tag_response.status_code == 200
    tag_payload = tag_response.json()["data"]
    assert tag_payload["succeeded"] == 2

    owner_response = client.post(
        f"/api/v1/projects/{project_id}/assets/bulk",
        json={
            "asset_ids": [first.id],
            "action": "change_owner",
            "owner": "SecOps Team",
        },
        headers=headers,
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["data"]["succeeded"] == 1

    archive_response = client.post(
        f"/api/v1/projects/{project_id}/assets/bulk",
        json={"asset_ids": [second.id], "action": "archive"},
        headers=headers,
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["succeeded"] == 1

    db.expire_all()
    archived = get_asset_by_id(db, project_id=project_id, asset_id=uuid.UUID(second.id))
    assert archived is not None
    assert archived.status == AssetStatus.ARCHIVED


def test_bulk_export_and_delete(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="bulk-export@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    asset = create_website_asset(db, membership, project_id=project_id, name="Export Me")
    db.commit()

    export_response = client.post(
        f"/api/v1/projects/{project_id}/assets/bulk",
        json={"asset_ids": [asset.id], "action": "export"},
        headers=headers,
    )
    assert export_response.status_code == 200
    export_payload = export_response.json()["data"]
    assert export_payload["succeeded"] == 1
    assert len(export_payload["export_items"]) == 1
    assert export_payload["export_items"][0]["name"] == "Export Me"

    delete_response = client.post(
        f"/api/v1/projects/{project_id}/assets/bulk",
        json={"asset_ids": [asset.id], "action": "delete"},
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["succeeded"] == 1

    db.expire_all()
    deleted = get_asset_by_id(
        db,
        project_id=project_id,
        asset_id=uuid.UUID(asset.id),
        include_deleted=True,
    )
    assert deleted is not None
    assert deleted.status == AssetStatus.DELETED
