from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from app.scans.enums import ScanStatus
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def _complete_scan(db, *, scan, project_id, asset_id) -> None:  # noqa: ARG001
    from app.scans.lifecycle import transition_scan_status

    transition_scan_status(scan, status=ScanStatus.COMPLETED)
    db.add(scan)


def test_dns_txt_verification_and_scan_gate(client, db, monkeypatch) -> None:
    ctx = bootstrap_org_context(db, client, email="verify-dns@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Example Domain",
            "type": "domain",
            "status": "active",
            "metadata": {"domain": "example.com"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    asset = create_response.json()["data"]
    asset_id = uuid.UUID(asset["id"])

    challenge = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/verification/challenge",
        json={"method": "dns_txt"},
        headers=headers,
    )
    assert challenge.status_code == 200, challenge.text
    token = challenge.json()["data"]["challenge_token"]

    class _TxtAnswer:
        strings = [f"ownership={token}".encode()]

    monkeypatch.setattr(
        "app.assets.services.verification_service.dns.resolver.resolve",
        lambda *args, **kwargs: [_TxtAnswer()],
    )

    verify = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/verification/verify",
        headers=headers,
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["data"]["status"] == "verified"

    create_scan = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        json={"scan_type": "quick"},
        headers=headers,
    )
    assert create_scan.status_code == 201, create_scan.text
    scan_id = create_scan.json()["data"]["id"]
    with patch(
        "app.scans.services.scan_executor.scan_orchestrator.execute",
        side_effect=_complete_scan,
    ):
        with patch("app.scans.services.scan_executor.risk_engine.recalculate_after_scan"):
            run_response = client.post(
                f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/{scan_id}/run",
                headers=headers,
            )
    assert run_response.status_code == 200


def test_pending_verification_blocks_scan(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="verify-http@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    asset = create_website_asset(
        db, ctx["membership"], project_id=project_id, url="https://verify.example.com"
    )
    asset_id = uuid.UUID(asset.id)

    challenge = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/verification/challenge",
        json={"method": "http"},
        headers=headers,
    )
    assert challenge.status_code == 200, challenge.text

    create_scan = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        json={"scan_type": "quick"},
        headers=headers,
    )
    assert create_scan.status_code in {400, 422}
    body = create_scan.json()
    assert body["success"] is False
    assert "mandatory" in body["error"]["message"].lower()


def test_website_scan_requires_verified_ownership(client, db) -> None:
    ctx = bootstrap_org_context(db, client, email="verify-required@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    headers = ctx["org_headers"]

    create_response = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={
            "name": "Unverified Website",
            "type": "website",
            "status": "active",
            "metadata": {"url": "https://unverified.example.com"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    asset_id = create_response.json()["data"]["id"]

    scan_response = client.post(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
        json={"scan_type": "quick"},
        headers=headers,
    )
    assert scan_response.status_code in {400, 422}
    payload = scan_response.json()
    assert payload["success"] is False
    assert "mandatory" in payload["error"]["message"].lower()
