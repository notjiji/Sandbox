"""Server monitoring agent enrollment, ingest, alerts, and RBAC."""

from __future__ import annotations

import uuid

import pytest

from app.monitoring.enums import AlertStatus
from app.monitoring.models import MonitoringAlert
from tests.support import bootstrap_org_context, create_website_asset, invite_and_accept_member

pytestmark = pytest.mark.integration


def _create_asset(client, project_id, headers, **payload):
    response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _create_server(
    client,
    project_id,
    headers,
    *,
    name: str = "Ubuntu VPS",
    hostname: str = "vps-01",
    address: str = "203.0.113.10",
    domain: str = "example.test",
):
    domain_asset = _create_asset(
        client,
        project_id,
        headers,
        name=domain,
        type="domain",
        status="active",
        metadata={"domain": domain},
    )
    public_ip = _create_asset(
        client,
        project_id,
        headers,
        name=f"IP {address}",
        type="public_ip",
        status="active",
        parent_id=domain_asset["id"],
        metadata={"address": address},
        allow_private_ip=True,
    )
    return _create_asset(
        client,
        project_id,
        headers,
        name=name,
        type="server",
        status="active",
        parent_id=public_ip["id"],
        metadata={
            "hostname": hostname,
            "os": "Ubuntu 24.04",
            "connection_type": "agent",
        },
    )


def _ingest_payload(**overrides):
    payload = {
        "hostname": "vps-01",
        "agent_version": "1.0.0",
        "metrics": {
            "cpu_usage": 12.0,
            "cpu_percent": 12.0,
            "load_1m": 0.2,
            "load_avg": [0.2, 0.3, 0.1],
            "cores": 4,
            "total_mb": 4096,
            "used_mb": 1600,
            "available_mb": 2496,
            "usage_percent": 40.0,
            "ram_percent": 40.0,
            "ram_used_mb": 1600,
            "ram_total_mb": 4096,
            "disks": [
                {
                    "filesystem": "/",
                    "total_gb": 40.0,
                    "used_gb": 22.0,
                    "available_gb": 18.0,
                    "usage_percent": 55.0,
                }
            ],
            "disk_percent": 55.0,
            "disk_used_gb": 22.0,
            "disk_total_gb": 40.0,
            "uptime_seconds": 3600,
            "boot_time": "2026-08-12T10:00:00+00:00",
            "last_reboot_at": "2026-08-12T10:00:00+00:00",
            "process_count": 2,
            "processes": [{"pid": 1, "name": "systemd", "rss_mb": 12.0}],
        },
        "security": {
            "firewall": {"enabled": True, "backend": "ufw"},
            "ssh": {"permit_root_login": False, "password_authentication": False, "port": 22},
            "fail2ban": {"enabled": True, "jails": ["sshd"]},
            "docker": {"installed": True, "running": True, "containers": 2},
            "updates": {"available": 0, "security": 0},
            "system": {"os": "Linux", "hostname": "vps-01"},
        },
    }
    payload.update(overrides)
    return payload


def _enroll(client, project_id, asset_id, headers):
    response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/monitoring/enroll",
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _register(client, enrollment_token: str):
    response = client.post(
        "/api/v1/monitoring/register",
        json={"enrollment_token": enrollment_token, "hostname": "vps-01", "agent_version": "1.0.0"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_enroll_register_and_overview(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="mon-owner@example.com")
    project_id = ctx["project"]["id"]
    headers = ctx["org_headers"]
    server = _create_server(client, project_id, headers)

    enrollment = _enroll(client, project_id, server["id"], headers)
    token = enrollment["enrollment_token"]
    assert token.startswith("sbe_")
    assert "SANDBOX_ENROLLMENT_TOKEN=" in enrollment["install_command"]
    assert "install.sh" in enrollment["install_command"]
    assert enrollment["python_command"].startswith("SANDBOX_API_URL=")

    script = client.get("/api/v1/monitoring/install.sh")
    assert script.status_code == 200
    assert "SANDBOX_ENROLLMENT_TOKEN" in script.text

    blocked = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 401

    registered = _register(client, token)
    credential = registered["credential"]
    assert credential.startswith("sba_")
    assert registered["asset_id"] == server["id"]

    reused = client.post(
        "/api/v1/monitoring/register",
        json={"enrollment_token": token, "hostname": "vps-01"},
    )
    assert reused.status_code == 401

    ingest = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers={"Authorization": f"Bearer {credential}"},
    )
    assert ingest.status_code == 200, ingest.text
    assert ingest.json()["data"]["accepted"] is True
    assert ingest.json()["data"]["agent_status"] == "online"
    assert ingest.json()["data"]["alerts_open"] == 0

    overview = client.get(
        f"/api/v1/projects/{project_id}/assets/{server['id']}/monitoring",
        headers=headers,
    )
    assert overview.status_code == 200, overview.text
    data = overview.json()["data"]
    assert data["agent"]["status"] == "online"
    assert data["metrics"]["cpu_usage"] == 12.0
    assert data["metrics"]["cores"] == 4
    assert data["metrics"]["load_1m"] == 0.2
    assert data["metrics"]["available_mb"] == 2496
    assert len(data["metrics"]["disks"]) == 1
    assert data["security"]["firewall"]["enabled"] is True
    assert data["latest"]["disk_percent"] == 55.0
    assert len(data["history"]) >= 1

    org = client.get("/api/v1/organizations/current/monitoring/overview", headers=headers)
    assert org.status_code == 200, org.text
    summary = org.json()["data"]
    assert summary["agents_online"] == 1
    assert summary["open_alerts"] == 0
    assert summary["servers"][0]["asset_id"] == server["id"]


def test_each_server_has_its_own_credential(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="mon-multi@example.com")
    project_id = ctx["project"]["id"]
    headers = ctx["org_headers"]
    server_a = _create_server(client, project_id, headers, name="Server A")
    server_b = _create_server(
        client,
        project_id,
        headers,
        name="Server B",
        hostname="vps-02",
        address="203.0.113.11",
        domain="other.test",
    )

    cred_a = _register(client, _enroll(client, project_id, server_a["id"], headers)["enrollment_token"])[
        "credential"
    ]
    cred_b = _register(client, _enroll(client, project_id, server_b["id"], headers)["enrollment_token"])[
        "credential"
    ]
    assert cred_a != cred_b

    ok_a = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers={"Authorization": f"Bearer {cred_a}"},
    )
    ok_b = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(hostname="vps-02"),
        headers={"Authorization": f"Bearer {cred_b}"},
    )
    assert ok_a.status_code == 200
    assert ok_b.status_code == 200

    client.post(
        f"/api/v1/projects/{project_id}/assets/{server_a['id']}/monitoring/revoke",
        headers=headers,
    )
    revoked_a = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers={"Authorization": f"Bearer {cred_a}"},
    )
    still_b = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(hostname="vps-02"),
        headers={"Authorization": f"Bearer {cred_b}"},
    )
    assert revoked_a.status_code == 401
    assert still_b.status_code == 200


def test_ingest_opens_and_resolves_alerts(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="mon-alerts@example.com")
    project_id = ctx["project"]["id"]
    headers = ctx["org_headers"]
    server = _create_server(client, project_id, headers)
    credential = _register(
        client,
        _enroll(client, project_id, server["id"], headers)["enrollment_token"],
    )["credential"]

    hot = _ingest_payload()
    hot["metrics"]["cpu_usage"] = 95.0
    hot["metrics"]["cpu_percent"] = 95.0
    hot["metrics"]["disks"] = [
        {"filesystem": "/", "usage_percent": 97.0, "total_gb": 40, "used_gb": 39, "available_gb": 1}
    ]
    hot["metrics"]["disk_percent"] = 97.0
    hot["security"]["firewall"] = {"enabled": False, "backend": "ufw"}
    hot["security"]["ssh"] = {
        "permit_root_login": True,
        "password_authentication": True,
        "port": 22,
    }
    first = client.post(
        "/api/v1/monitoring/ingest",
        json=hot,
        headers={"Authorization": f"Bearer {credential}"},
    )
    assert first.status_code == 200
    assert first.json()["data"]["alerts_open"] >= 3

    overview = client.get(
        f"/api/v1/projects/{project_id}/assets/{server['id']}/monitoring",
        headers=headers,
    ).json()["data"]
    open_codes = {alert["alert_code"] for alert in overview["alerts"] if alert["status"] == "open"}
    assert "CPU_HIGH" in open_codes
    assert "DISK_CRITICAL__root" in open_codes or "DISK_CRITICAL__" in str(open_codes)
    assert "FIREWALL_INACTIVE" in open_codes

    cool = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers={"Authorization": f"Bearer {credential}"},
    )
    assert cool.status_code == 200
    assert cool.json()["data"]["alerts_open"] == 0
    remaining_open = (
        db.query(MonitoringAlert)
        .filter(
            MonitoringAlert.asset_id == uuid.UUID(server["id"]),
            MonitoringAlert.status == AlertStatus.OPEN,
        )
        .count()
    )
    assert remaining_open == 0


def test_viewer_can_read_but_cannot_enroll(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="mon-rbac-owner@example.com")
    project_id = owner_ctx["project"]["id"]
    server = _create_server(client, project_id, owner_ctx["org_headers"])
    viewer = invite_and_accept_member(
        db,
        client,
        owner_ctx,
        email="mon-rbac-viewer@example.com",
        role="viewer",
    )

    read = client.get(
        f"/api/v1/projects/{project_id}/assets/{server['id']}/monitoring",
        headers=viewer["org_headers"],
    )
    assert read.status_code == 200

    enroll = client.post(
        f"/api/v1/projects/{project_id}/assets/{server['id']}/monitoring/enroll",
        headers=viewer["org_headers"],
    )
    assert enroll.status_code == 403


def test_manager_cannot_enroll(client, db) -> None:
    owner_ctx = bootstrap_org_context(db, client, email="mon-mgr-owner@example.com")
    project_id = owner_ctx["project"]["id"]
    server = _create_server(client, project_id, owner_ctx["org_headers"])
    manager = invite_and_accept_member(
        db,
        client,
        owner_ctx,
        email="mon-mgr@example.com",
        role="manager",
    )
    enroll = client.post(
        f"/api/v1/projects/{project_id}/assets/{server['id']}/monitoring/enroll",
        headers=manager["org_headers"],
    )
    assert enroll.status_code == 403


def test_website_cannot_enroll(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="mon-website@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset.id}/monitoring/enroll",
        headers=ctx["org_headers"],
    )
    assert response.status_code == 422


def test_ingest_requires_agent_token(client, db) -> None:
    missing = client.post("/api/v1/monitoring/ingest", json=_ingest_payload())
    assert missing.status_code == 401

    ctx = bootstrap_org_context(db, client, email="mon-jwt@example.com")
    jwt_ingest = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers=ctx["headers"],
    )
    assert jwt_ingest.status_code == 401


def test_revoke_rejects_old_token(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="mon-revoke@example.com")
    project_id = ctx["project"]["id"]
    headers = ctx["org_headers"]
    server = _create_server(client, project_id, headers)
    credential = _register(
        client,
        _enroll(client, project_id, server["id"], headers)["enrollment_token"],
    )["credential"]

    revoke = client.post(
        f"/api/v1/projects/{project_id}/assets/{server['id']}/monitoring/revoke",
        headers=headers,
    )
    assert revoke.status_code == 200

    ingest = client.post(
        "/api/v1/monitoring/ingest",
        json=_ingest_payload(),
        headers={"Authorization": f"Bearer {credential}"},
    )
    assert ingest.status_code == 401


def test_org_isolation_for_monitoring(client, db) -> None:
    ctx_a = bootstrap_org_context(db, client, email="mon-iso-a@example.com", org_name="Org A")
    ctx_b = bootstrap_org_context(db, client, email="mon-iso-b@example.com", org_name="Org B")
    server = _create_server(client, ctx_a["project"]["id"], ctx_a["org_headers"])
    client.post(
        f"/api/v1/projects/{ctx_a['project']['id']}/assets/{server['id']}/monitoring/enroll",
        headers=ctx_a["org_headers"],
    )

    peek = client.get(
        f"/api/v1/projects/{ctx_a['project']['id']}/assets/{server['id']}/monitoring",
        headers=ctx_b["org_headers"],
    )
    assert peek.status_code in {403, 404}

    enroll = client.post(
        f"/api/v1/projects/{ctx_a['project']['id']}/assets/{server['id']}/monitoring/enroll",
        headers=ctx_b["org_headers"],
    )
    assert enroll.status_code in {403, 404}
