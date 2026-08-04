"""Batch enrichment for asset summaries — security and lifecycle context."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.risk.repositories.risk_repository import get_latest_asset_risks_for_organization
from app.scans.enums import ScanStatus
from app.scans.models import Scan


@dataclass
class AssetSecurityStats:
    current_risk_score: float | None = None
    security_grade: str | None = None
    last_scan_at: datetime | None = None
    last_successful_scan_at: datetime | None = None
    last_scan_status: str | None = None
    findings_count: int = 0
    critical_findings_count: int = 0


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

    return stats
