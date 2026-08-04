"""Asset relationship and hierarchy integration tests."""

from __future__ import annotations

import uuid

import pytest

from tests.support import bootstrap_org_context

pytestmark = pytest.mark.integration


def _create_asset(client, project_id, headers, **payload):
    response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_infrastructure_dependency_chain(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="chain@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    domain = _create_asset(
        client,
        project_id,
        headers,
        name="vinca.family",
        type="domain",
        status="active",
        metadata={"domain": "vinca.family"},
    )
    public_ip = _create_asset(
        client,
        project_id,
        headers,
        name="Primary IP",
        type="public_ip",
        status="active",
        parent_id=domain["id"],
        metadata={"address": "104.0.0.1"},
        allow_private_ip=True,
    )
    server = _create_asset(
        client,
        project_id,
        headers,
        name="Ubuntu VPS",
        type="server",
        status="active",
        parent_id=public_ip["id"],
        metadata={
            "hostname": "vps-01",
            "os": "Ubuntu 24.04",
            "connection_type": "ssh",
        },
    )
    docker = _create_asset(
        client,
        project_id,
        headers,
        name="Docker",
        type="docker_host",
        status="active",
        parent_id=server["id"],
        metadata={"hostname": "docker-host"},
    )
    website = _create_asset(
        client,
        project_id,
        headers,
        name="Nginx",
        type="website",
        status="active",
        parent_id=docker["id"],
        metadata={"url": "https://vinca.family"},
    )

    rel_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{website['id']}/relationships",
        headers=headers,
    )
    assert rel_response.status_code == 200
    relationships = rel_response.json()["data"]

    assert relationships["parent"]["id"] == docker["id"]
    assert len(relationships["ancestors"]) == 4
    assert relationships["ancestors"][0]["id"] == domain["id"]
    assert relationships["ancestors"][-1]["id"] == docker["id"]
    assert relationships["descendants_count"] == 0

    graph = relationships["graph"]
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4
    current_nodes = [node for node in graph["nodes"] if node["is_current"]]
    assert len(current_nodes) == 1
    assert current_nodes[0]["id"] == website["id"]


def test_asset_links(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="links@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    source = _create_asset(
        client,
        project_id,
        headers,
        name="API Gateway",
        type="api_endpoint",
        status="active",
        metadata={"endpoint": "https://api.example.com"},
    )
    target = _create_asset(
        client,
        project_id,
        headers,
        name="Auth Service",
        type="website",
        status="active",
        metadata={"url": "https://auth.example.com"},
    )

    link_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{source['id']}/links",
        json={
            "target_asset_id": target["id"],
            "link_type": "depends_on",
            "label": "Authentication",
        },
        headers=headers,
    )
    assert link_response.status_code == 201
    link = link_response.json()["data"]
    assert link["link_type"] == "depends_on"
    assert link["asset"]["id"] == target["id"]

    rel_response = client.get(
        f"/api/v1/projects/{project_id}/assets/{source['id']}/relationships",
        headers=headers,
    )
    assert rel_response.status_code == 200
    relationships = rel_response.json()["data"]
    assert len(relationships["links"]) == 1
    assert relationships["links"][0]["direction"] == "outbound"

    delete_response = client.delete(
        f"/api/v1/projects/{project_id}/assets/{source['id']}/links/{link['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 200
