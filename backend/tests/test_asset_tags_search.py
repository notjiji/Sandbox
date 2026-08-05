"""Asset tag filter and saved filter tests."""

from __future__ import annotations

import uuid

import pytest

from app.assets.enums import AssetCriticality, AssetEnvironment, AssetStatus, AssetType
from app.assets.schemas import CreateAssetRequest
from app.assets.services import create_project_asset
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def test_multi_tag_filter_and_sort(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-tags@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]

    production_critical = create_project_asset(
        db,
        membership,
        project_id=project_id,
        body=CreateAssetRequest(
            name="Prod Critical Site",
            type=AssetType.WEBSITE,
            status=AssetStatus.ACTIVE,
            environment=AssetEnvironment.PRODUCTION,
            criticality=AssetCriticality.CRITICAL,
            metadata={"url": "https://prod-critical.example.com"},
            tags=["customer"],
        ),
    )
    production_medium = create_project_asset(
        db,
        membership,
        project_id=project_id,
        body=CreateAssetRequest(
            name="Prod Medium Site",
            type=AssetType.WEBSITE,
            status=AssetStatus.ACTIVE,
            environment=AssetEnvironment.PRODUCTION,
            criticality=AssetCriticality.MEDIUM,
            metadata={"url": "https://prod-medium.example.com"},
            tags=["ubuntu", "docker"],
        ),
    )
    db.commit()

    matched = client.get(
        f"/api/v1/projects/{project_id}/assets?tags=production,critical,website",
        headers=headers,
    )
    assert matched.status_code == 200
    items = matched.json()["data"]["items"]
    assert matched.json()["data"]["total"] == 1
    assert items[0]["name"] == "Prod Critical Site"

    ubuntu_only = client.get(
        f"/api/v1/projects/{project_id}/assets?tags=ubuntu",
        headers=headers,
    )
    assert ubuntu_only.json()["data"]["total"] == 1
    assert ubuntu_only.json()["data"]["items"][0]["name"] == "Prod Medium Site"

    # Flat name sort applies when listing roots only; the default project list
    # keeps hierarchy groups together, so sort=name is tertiary there.
    sorted_response = client.get(
        f"/api/v1/projects/{project_id}/assets?sort=name&order=desc&roots_only=true",
        headers=headers,
    )
    assert sorted_response.status_code == 200
    names = [item["name"] for item in sorted_response.json()["data"]["items"]]
    assert names == ["Prod Medium Site", "Prod Critical Site"]

    tags_response = client.get(
        f"/api/v1/projects/{project_id}/assets/tags",
        headers=headers,
    )
    assert tags_response.status_code == 200
    tag_names = {item["tag"] for item in tags_response.json()["data"]["items"]}
    assert "production" in tag_names
    assert "ubuntu" in tag_names


def test_saved_filters_crud(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="asset-saved-filters@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]
    membership = ctx["membership"]
    create_website_asset(db, membership, project_id=project_id)
    db.commit()

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets/saved-filters",
        json={
            "name": "Production critical websites",
            "filters": {
                "search": "",
                "tags": ["production", "critical", "website"],
                "type": "",
                "status": "",
                "environment": "",
                "criticality": "",
                "asset_category": "",
                "sort": "name",
                "order": "asc",
            },
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    saved = create_response.json()["data"]
    assert saved["name"] == "Production critical websites"
    assert saved["filters"]["tags"] == ["production", "critical", "website"]

    list_response = client.get(
        f"/api/v1/projects/{project_id}/assets/saved-filters",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]["items"]) == 1

    delete_response = client.delete(
        f"/api/v1/projects/{project_id}/assets/saved-filters/{saved['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    empty_response = client.get(
        f"/api/v1/projects/{project_id}/assets/saved-filters",
        headers=headers,
    )
    assert empty_response.json()["data"]["items"] == []
