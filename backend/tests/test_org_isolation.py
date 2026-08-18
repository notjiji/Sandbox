"""Cross-organization isolation tests."""

from __future__ import annotations

import uuid

import pytest

from app.ai.repositories.conversation_repository import create_conversation
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.scans.enums import ScanType
from app.scans.repositories.scan_repository import create_scan
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def _blocked(response) -> None:
    assert response.status_code in {403, 404}, response.text
    body = response.json()
    assert body.get("success") is False


def _pair(db, client, prefix: str):
    org_a = bootstrap_org_context(
        db, client, email=f"{prefix}-a@example.com", org_name=f"{prefix} A"
    )
    org_b = bootstrap_org_context(
        db, client, email=f"{prefix}-b@example.com", org_name=f"{prefix} B"
    )
    return org_a, org_b


def test_cannot_access_other_org_project(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="iso-a@example.com", org_name="Org A")
    org_b = bootstrap_org_context(db, client, email="iso-b@example.com", org_name="Org B")

    response = client.get(
        f"/api/v1/projects/{org_b['project']['id']}",
        headers=org_a["org_headers"],
    )
    assert response.status_code == 404, response.text


def test_cannot_access_other_org_asset_risk(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="risk-a@example.com", org_name="Risk Org A")
    org_b = bootstrap_org_context(db, client, email="risk-b@example.com", org_name="Risk Org B")

    asset = create_website_asset(
        db,
        org_b["membership"],
        project_id=uuid.UUID(org_b["project"]["id"]),
        name="Foreign Asset",
    )
    db.commit()

    response = client.get(
        f"/api/v1/organizations/risk/assets/{asset.id}",
        headers=org_a["org_headers"],
    )
    assert response.status_code == 404, response.text


def test_archived_organization_blocks_org_scoped_routes(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="archived-org@example.com")

    archive_response = client.patch(
        "/api/v1/organizations/current/archive",
        headers=ctx["org_headers"],
    )
    assert archive_response.status_code == 200, archive_response.text

    projects_response = client.get(
        "/api/v1/projects",
        headers=ctx["org_headers"],
    )
    assert projects_response.status_code == 404, projects_response.text


def test_cannot_revoke_other_org_invite(client, db) -> None:
    org_a = bootstrap_org_context(db, client, email="invite-a@example.com", org_name="Invite A")
    org_b = bootstrap_org_context(db, client, email="invite-b@example.com", org_name="Invite B")

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": "outsider@example.com", "role": "viewer"},
        headers=org_b["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text
    invite_id = invite_response.json()["data"]["invite_id"]

    revoke_response = client.delete(
        f"/api/v1/organizations/current/invites/{invite_id}",
        headers=org_a["org_headers"],
    )
    assert revoke_response.status_code == 404, revoke_response.text


def test_project_patch_rejects_is_active_toggle(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="patch-project@example.com")
    project_id = ctx["project"]["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"is_active": False},
        headers=ctx["org_headers"],
    )
    assert response.status_code == 422, response.text
    assert "archive or restore" in response.json()["error"]["message"].lower()


def test_org_header_spoof_is_forbidden(client, db) -> None:
    org_a, org_b = _pair(db, client, "spoof")
    spoofed = {**org_a["headers"], "X-Organization-ID": org_b["organization"]["id"]}

    response = client.get("/api/v1/organizations/current", headers=spoofed)
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_cannot_read_other_org_asset(client, db) -> None:
    org_a, org_b = _pair(db, client, "asset-idor")
    project_b = uuid.UUID(org_b["project"]["id"])
    asset = create_website_asset(db, org_b["membership"], project_id=project_b, name="Secret Site")
    db.commit()

    _blocked(
        client.get(
            f"/api/v1/projects/{project_b}/assets/{asset.id}",
            headers=org_a["org_headers"],
        )
    )
    _blocked(
        client.delete(
            f"/api/v1/projects/{project_b}/assets/{asset.id}",
            headers=org_a["org_headers"],
        )
    )


def test_cannot_read_other_org_project(client, db) -> None:
    org_a, org_b = _pair(db, client, "project-idor")
    _blocked(
        client.get(
            f"/api/v1/projects/{org_b['project']['id']}",
            headers=org_a["org_headers"],
        )
    )
    _blocked(
        client.patch(
            f"/api/v1/projects/{org_b['project']['id']}",
            json={"name": "Taken Over"},
            headers=org_a["org_headers"],
        )
    )


def test_cannot_read_other_org_scan(client, db) -> None:
    org_a, org_b = _pair(db, client, "scan-idor")
    project_b = uuid.UUID(org_b["project"]["id"])
    asset = create_website_asset(db, org_b["membership"], project_id=project_b)
    scan = create_scan(
        db,
        project_id=project_b,
        asset_id=uuid.UUID(asset.id),
        scan_type=ScanType.QUICK,
        created_by=org_b["membership"].user_id,
    )
    db.commit()

    _blocked(
        client.get(
            f"/api/v1/projects/{project_b}/assets/{asset.id}/scans/{scan.id}",
            headers=org_a["org_headers"],
        )
    )
    _blocked(
        client.post(
            f"/api/v1/projects/{project_b}/assets/{asset.id}/scans/{scan.id}/run",
            headers=org_a["org_headers"],
        )
    )


def test_cannot_read_other_org_finding(client, db) -> None:
    org_a, org_b = _pair(db, client, "finding-idor")
    project_b = uuid.UUID(org_b["project"]["id"])
    asset = create_website_asset(db, org_b["membership"], project_id=project_b)
    scan = create_scan(
        db,
        project_id=project_b,
        asset_id=uuid.UUID(asset.id),
        scan_type=ScanType.QUICK,
        created_by=org_b["membership"].user_id,
    )
    finding = create_finding(
        db,
        project_id=project_b,
        scan_id=scan.id,
        asset_id=uuid.UUID(asset.id),
        title="Secret finding",
        severity=FindingSeverity.HIGH,
        risk_score=30.0,
        status=FindingStatus.OPEN,
    )
    db.commit()

    _blocked(
        client.get(
            f"/api/v1/projects/{project_b}/findings/{finding.id}",
            headers=org_a["org_headers"],
        )
    )
    listed = client.get(
        f"/api/v1/projects/{org_a['project']['id']}/findings",
        headers=org_a["org_headers"],
    )
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()["data"]["items"]}
    assert str(finding.id) not in ids


def test_cannot_read_other_org_report(client, db) -> None:
    org_a, org_b = _pair(db, client, "report-idor")
    project_b = uuid.UUID(org_b["project"]["id"])
    asset = create_website_asset(db, org_b["membership"], project_id=project_b)
    scan = create_scan(
        db,
        project_id=project_b,
        asset_id=uuid.UUID(asset.id),
        scan_type=ScanType.QUICK,
        created_by=org_b["membership"].user_id,
    )
    create_finding(
        db,
        project_id=project_b,
        scan_id=scan.id,
        asset_id=uuid.UUID(asset.id),
        title="Report finding",
        severity=FindingSeverity.MEDIUM,
        risk_score=15.0,
        status=FindingStatus.OPEN,
    )
    db.commit()

    created = client.post(
        f"/api/v1/projects/{project_b}/assets/{asset.id}/reports",
        json={"report_type": "executive", "scan_id": str(scan.id), "generate": True},
        headers=org_b["org_headers"],
    )
    assert created.status_code == 201, created.text
    report_id = created.json()["data"]["id"]

    _blocked(
        client.get(
            f"/api/v1/projects/{project_b}/assets/{asset.id}/reports/{report_id}",
            headers=org_a["org_headers"],
        )
    )
    _blocked(
        client.get(
            f"/api/v1/projects/{project_b}/assets/{asset.id}/reports/{report_id}/download",
            headers=org_a["org_headers"],
        )
    )


def test_cannot_read_other_org_ai_conversation(client, db) -> None:
    org_a, org_b = _pair(db, client, "ai-idor")
    conversation = create_conversation(
        db,
        organization_id=uuid.UUID(org_b["organization"]["id"]),
        user_id=org_b["membership"].user_id,
        title="Org B secret chat",
    )
    db.commit()

    _blocked(
        client.get(
            f"/api/v1/organizations/ai/conversations/{conversation.id}",
            headers=org_a["org_headers"],
        )
    )
    listed = client.get("/api/v1/organizations/ai/conversations", headers=org_a["org_headers"])
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()["data"]["items"]}
    assert str(conversation.id) not in ids


def test_cannot_read_other_org_audit_logs(client, db) -> None:
    org_a, org_b = _pair(db, client, "audit-idor")
    foreign = client.get("/api/v1/audit-logs", headers=org_b["org_headers"], params={"limit": 20})
    assert foreign.status_code == 200, foreign.text
    foreign_items = foreign.json()["data"]["items"]
    assert foreign_items
    foreign_id = foreign_items[0]["id"]
    foreign_org = org_b["organization"]["id"]

    _blocked(
        client.get(f"/api/v1/audit-logs/{foreign_id}", headers=org_a["org_headers"])
    )
    listed = client.get("/api/v1/audit-logs", headers=org_a["org_headers"], params={"limit": 100})
    assert listed.status_code == 200, listed.text
    for item in listed.json()["data"]["items"]:
        assert item["id"] != foreign_id
        if item.get("organization_id"):
            assert item["organization_id"] != foreign_org


def test_cannot_read_other_org_monitoring_data(client, db) -> None:
    from tests.test_monitoring import _create_server

    org_a, org_b = _pair(db, client, "mon-idor")
    server = _create_server(client, org_b["project"]["id"], org_b["org_headers"])
    enroll = client.post(
        f"/api/v1/projects/{org_b['project']['id']}/assets/{server['id']}/monitoring/enroll",
        headers=org_b["org_headers"],
    )
    assert enroll.status_code == 201, enroll.text

    _blocked(
        client.get(
            f"/api/v1/projects/{org_b['project']['id']}/assets/{server['id']}/monitoring",
            headers=org_a["org_headers"],
        )
    )
    _blocked(
        client.get(
            f"/api/v1/projects/{org_b['project']['id']}/assets/{server['id']}/monitoring/metrics",
            headers=org_a["org_headers"],
        )
    )

