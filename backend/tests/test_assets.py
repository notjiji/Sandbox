"""Asset CRUD API tests."""

from __future__ import annotations

import uuid

import pytest

from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_asset_crud_flow(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-user@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Corporate Site",
            "type": "website",
            "status": "active",
            "environment": "production",
            "criticality": "high",
            "metadata": {"url": "https://corp.example.com"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    asset_id = created["id"]
    assert created["name"] == "Corporate Site"

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets",
        headers=headers,
    )
    assert list_response.status_code == 200
    listed = list_response.json()["data"]
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == asset_id

    get_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["metadata"]["url"] == "https://corp.example.com"

    update_response = client.put(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        json={"name": "Corporate Portal", "criticality": "critical"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Corporate Portal"

    archive_response = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/archive",
        headers=headers,
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["status"] == "archived"

    restore_response = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/restore",
        headers=headers,
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["status"] == "active"

    delete_response = client.delete(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True


def test_rich_asset_fields(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="rich-asset@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Payment API",
            "type": "api_endpoint",
            "status": "active",
            "environment": "production",
            "criticality": "critical",
            "owner": "Payments Team",
            "external_identifier": "CMDB-9001",
            "business_unit": "Finance",
            "asset_category": "application",
            "metadata": {"endpoint": "https://pay.example.com/v1"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["external_identifier"] == "CMDB-9001"
    assert created["business_unit"] == "Finance"
    assert created["asset_category"] == "application"
    assert created["organization_name"] is not None
    assert created["project_name"] is not None
    assert "created_at" in created
    assert created["created_by"] is not None

    asset_id = created["id"]
    archive_response = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/archive",
        headers=headers,
    )
    assert archive_response.status_code == 200
    archived = archive_response.json()["data"]
    assert archived["status"] == "archived"
    assert archived["archived_at"] is not None
    assert archived["archived_by"] is not None


def test_create_asset_via_service(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-service@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])

    asset = create_website_asset(
        db,
        ctx["membership"],
        project_id=project_id,
        name="Service Asset",
        url="https://service.example.com",
    )
    assert asset.name == "Service Asset"
    assert asset.metadata["url"] == "https://service.example.com"
