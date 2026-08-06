"""Risk engine integration tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.core.risk_engine.engine import RiskEngine
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.risk.models import RiskRule
from app.scans.enums import ScanStatus, ScanType
from app.scans.repositories.scan_repository import create_scan, update_scan_status
from tests.support import bootstrap_org_context, create_website_asset

pytestmark = pytest.mark.integration


def _seed_scan(db, *, project_id: uuid.UUID, asset_id: uuid.UUID, user_id: uuid.UUID):
    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=ScanType.QUICK,
        created_by=user_id,
        selected_plugins=None,
    )
    update_scan_status(db, scan, status=ScanStatus.QUEUED)
    update_scan_status(db, scan, status=ScanStatus.RUNNING)
    update_scan_status(db, scan, status=ScanStatus.COMPLETED)
    return scan


def test_calculate_asset_risk_from_open_findings(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="risk-asset@example.com")
    project_id = uuid.UUID(ctx["project"]["id"])
    asset = create_website_asset(db, ctx["membership"], project_id=project_id)
    asset_id = uuid.UUID(asset.id)
    scan = _seed_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        user_id=ctx["membership"].user_id,
    )
    db.commit()

    create_finding(
        db,
        project_id=project_id,
        scan_id=scan.id,
        asset_id=asset_id,
        title="Missing CSP",
        severity=FindingSeverity.HIGH,
        risk_score=25.0,
        status=FindingStatus.OPEN,
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan.id,
        asset_id=asset_id,
        title="Resolved issue",
        severity=FindingSeverity.CRITICAL,
        risk_score=50.0,
        status=FindingStatus.RESOLVED,
    )
    db.commit()

    engine = RiskEngine()
    result = engine.calculate_asset_risk(db, asset_id=asset_id, scan_id=scan.id)

    assert result.scanned is True
    assert result.total_risk == 25.0
    assert result.score == 75.0
    assert result.high_count == 1
    assert result.critical_count == 0


def test_resolve_finding_uses_configured_risk_rule(db) -> None:
    db.add(
        RiskRule(
            plugin="http_headers",
            finding_code="HTTP_NO_CSP",
            title="Missing CSP",
            severity=FindingSeverity.HIGH,
            score=30.0,
            enabled=True,
        )
    )
    db.commit()

    from app.plugins.output import PluginFinding, PluginFindingStatus

    engine = RiskEngine()
    resolved = engine.resolve_finding(
        db,
        plugin_finding=PluginFinding(
            plugin="http_headers",
            rule_id="HTTP_NO_CSP",
            asset_id="00000000-0000-4000-8000-000000000001",
            title="Missing CSP",
            status=PluginFindingStatus.FAILED,
            evidence="header absent",
            detected_at=datetime.now(UTC),
        ),
    )

    assert resolved is not None
    assert resolved.risk_score == 30.0
    assert resolved.severity == FindingSeverity.HIGH


def test_calculate_organization_risk_averages_scanned_assets(db, client) -> None:
    ctx = bootstrap_org_context(db, client, email="risk-org@example.com")
    org_id = uuid.UUID(ctx["organization"]["id"])
    project_id = uuid.UUID(ctx["project"]["id"])

    first = create_website_asset(
        db,
        ctx["membership"],
        project_id=project_id,
        name="Site A",
        url="https://a.example.com",
    )
    second = create_website_asset(
        db,
        ctx["membership"],
        project_id=project_id,
        name="Site B",
        url="https://b.example.com",
    )
    db.commit()

    engine = RiskEngine()
    scan_a = _seed_scan(
        db,
        project_id=project_id,
        asset_id=uuid.UUID(first.id),
        user_id=ctx["membership"].user_id,
    )
    scan_b = _seed_scan(
        db,
        project_id=project_id,
        asset_id=uuid.UUID(second.id),
        user_id=ctx["membership"].user_id,
    )
    db.commit()

    engine.calculate_asset_risk(
        db,
        asset_id=uuid.UUID(first.id),
        scan_id=scan_a.id,
        store=True,
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan_a.id,
        asset_id=uuid.UUID(first.id),
        title="Low issue",
        severity=FindingSeverity.LOW,
        risk_score=10.0,
    )
    db.commit()
    engine.calculate_asset_risk(db, asset_id=uuid.UUID(first.id), scan_id=scan_a.id, store=True)

    engine.calculate_asset_risk(
        db,
        asset_id=uuid.UUID(second.id),
        scan_id=scan_b.id,
        store=True,
    )
    create_finding(
        db,
        project_id=project_id,
        scan_id=scan_b.id,
        asset_id=uuid.UUID(second.id),
        title="Medium issue",
        severity=FindingSeverity.MEDIUM,
        risk_score=30.0,
    )
    db.commit()
    engine.calculate_asset_risk(db, asset_id=uuid.UUID(second.id), scan_id=scan_b.id, store=True)

    org_risk = engine.calculate_organization_risk(db, organization_id=org_id, store=True)

    assert org_risk.overall_score is not None
    assert org_risk.scanned_assets == 2
    assert org_risk.unscanned_assets == 0
    assert 80.0 <= org_risk.overall_score <= 95.0
