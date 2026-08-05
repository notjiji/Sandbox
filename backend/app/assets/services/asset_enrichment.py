"""Batch enrichment for asset summaries — security and lifecycle context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.assets.enums import AssetHealthStatus, AssetStatus
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.risk.repositories.risk_repository import get_latest_asset_risks_for_organization
from app.scans.enums import ScanStatus
from app.scans.models import Scan
from app.scans.schedule_models import AssetScanSchedule


@dataclass
class AssetSecurityStats:
    current_risk_score: float | None = None
    security_grade: str | None = None
    last_scan_at: datetime | None = None
    last_successful_scan_at: datetime | None = None
    last_scan_status: str | None = None
    findings_count: int = 0
    critical_findings_count: int = 0
    next_scan_at: datetime | None = None


def compute_health_status(
    lifecycle_status: AssetStatus,
    security: AssetSecurityStats,
) -> AssetHealthStatus:
    if lifecycle_status in (AssetStatus.DELETED, AssetStatus.ARCHIVED):
        return AssetHealthStatus.INACTIVE
    if lifecycle_status == AssetStatus.PENDING:
        return AssetHealthStatus.UNSCANNED

    has_scan_context = (
        security.last_scan_at is not None
        or security.last_successful_scan_at is not None
        or security.current_risk_score is not None
    )
    if not has_scan_context:
        return AssetHealthStatus.UNSCANNED
    if security.critical_findings_count > 0:
        return AssetHealthStatus.CRITICAL

    score = security.current_risk_score
    if score is not None and score < 60:
        return AssetHealthStatus.CRITICAL
    if score is not None and score < 80:
        return AssetHealthStatus.AT_RISK
    return AssetHealthStatus.HEALTHY


def card_security_score(security: AssetSecurityStats) -> int | None:
    if security.current_risk_score is None:
        return None
    return int(round(security.current_risk_score))


def card_last_scan(security: AssetSecurityStats) -> datetime | None:
    return security.last_successful_scan_at or security.last_scan_at


def load_security_stats_batch(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset_ids: list[uuid.UUID],
) -> dict[uuid.UUID, AssetSecurityStats]:
    if not asset_ids:
        return {}

    stats = {asset_id: AssetSecurityStats() for asset_id in asset_ids}

    risk_rows = get_latest_asset_risks_for_organization(db, organization_id=organization_id)
    for row in risk_rows:
        if row.asset_id not in stats:
            continue
        entry = stats[row.asset_id]
        entry.current_risk_score = row.score
        entry.security_grade = row.grade

    latest_scans = (
        db.query(Scan)
        .filter(Scan.asset_id.in_(asset_ids))
        .order_by(Scan.created_at.desc())
        .all()
    )
    for scan in latest_scans:
        entry = stats[scan.asset_id]
        if entry.last_scan_at is None:
            entry.last_scan_at = scan.created_at
            entry.last_scan_status = scan.status.value

    successful_scans = (
        db.query(Scan)
        .filter(Scan.asset_id.in_(asset_ids), Scan.status == ScanStatus.COMPLETED)
        .order_by(Scan.completed_at.desc().nullslast(), Scan.created_at.desc())
        .all()
    )
    for scan in successful_scans:
        entry = stats[scan.asset_id]
        if entry.last_successful_scan_at is None:
            entry.last_successful_scan_at = scan.completed_at or scan.created_at

    finding_counts = (
        db.query(
            Finding.asset_id,
            func.count(Finding.id),
            func.sum(
                case(
                    (Finding.severity == FindingSeverity.CRITICAL, 1),
                    else_=0,
                )
            ),
        )
        .filter(
            Finding.asset_id.in_(asset_ids),
            Finding.status == FindingStatus.OPEN,
        )
        .group_by(Finding.asset_id)
        .all()
    )
    for asset_id, total, critical in finding_counts:
        entry = stats[asset_id]
        entry.findings_count = int(total or 0)
        entry.critical_findings_count = int(critical or 0)

    schedule_rows = (
        db.query(
            AssetScanSchedule.asset_id,
            func.min(AssetScanSchedule.next_run_at),
        )
        .filter(
            AssetScanSchedule.asset_id.in_(asset_ids),
            AssetScanSchedule.enabled.is_(True),
            AssetScanSchedule.next_run_at.isnot(None),
        )
        .group_by(AssetScanSchedule.asset_id)
        .all()
    )
    for asset_id, next_run_at in schedule_rows:
        stats[asset_id].next_scan_at = next_run_at

    return stats
