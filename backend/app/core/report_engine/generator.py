"""Generate asset and project reports from live security data."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.assets.models import Asset
from app.assets.repositories.overview_repository import (
    count_asset_findings,
    list_asset_open_findings,
)
from app.core.report_engine.pdf import build_text_pdf
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.reports.enums import ReportType
from app.reports.models import Report
from app.risk.repositories.risk_repository import get_latest_asset_risk

REPORT_TYPE_LABELS = {
    ReportType.EXECUTIVE: "Executive",
    ReportType.TECHNICAL: "Technical",
    ReportType.WEEKLY: "Weekly",
    ReportType.MONTHLY: "Monthly",
}


def _storage_dir() -> Path:
    base = Path(__file__).resolve().parents[3] / "storage" / "reports"
    base.mkdir(parents=True, exist_ok=True)
    return base


def report_file_path(report_id: uuid.UUID) -> Path:
    return _storage_dir() / f"{report_id}.pdf"


def _report_lines(
    db: Session,
    *,
    report: Report,
    asset: Asset | None,
) -> list[str]:
    lines: list[str] = []
    lines.append(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Type: {REPORT_TYPE_LABELS.get(report.report_type, report.report_type.value)}")
    lines.append(f"Status: {report.status.value}")

    if asset is not None:
        lines.append("")
        lines.append(f"Asset: {asset.name} ({asset.type.value})")
        risk = get_latest_asset_risk(db, asset_id=asset.id)
        if risk:
            lines.append(f"Risk score: {risk.score:.1f} (grade {risk.grade})")
        open_count = count_asset_findings(db, asset_id=asset.id, status=FindingStatus.OPEN)
        total_count = count_asset_findings(db, asset_id=asset.id)
        critical_count = (
            db.query(Finding)
            .filter(
                Finding.asset_id == asset.id,
                Finding.status == FindingStatus.OPEN,
                Finding.severity == FindingSeverity.CRITICAL,
            )
            .count()
        )
        lines.append(f"Open findings: {open_count} ({critical_count} critical) of {total_count}")

        if report.report_type in {ReportType.EXECUTIVE, ReportType.WEEKLY, ReportType.MONTHLY}:
            lines.append("")
            lines.append("Top open findings:")
            findings = list_asset_open_findings(db, asset_id=asset.id, limit=8)
            if not findings:
                lines.append("  No open findings.")
            for finding in findings:
                lines.append(f"  - [{finding.severity.value}] {finding.title}")

        if report.report_type == ReportType.TECHNICAL:
            lines.append("")
            lines.append("Open findings (technical detail):")
            findings = (
                db.query(Finding)
                .filter(
                    Finding.asset_id == asset.id,
                    Finding.status == FindingStatus.OPEN,
                )
                .order_by(Finding.risk_score.desc())
                .limit(15)
                .all()
            )
            if not findings:
                lines.append("  No open findings.")
            for finding in findings:
                lines.append(
                    f"  - [{finding.severity.value}] {finding.title} "
                    f"(risk {finding.risk_score:.0f}, plugin {finding.plugin or 'n/a'})"
                )
                if finding.recommendation:
                    lines.append(f"    Recommendation: {finding.recommendation[:120]}")
    else:
        lines.append("")
        lines.append("Project-level report (no asset scope).")

    if report.description:
        lines.append("")
        lines.append(f"Notes: {report.description}")

    return lines


def generate_report_file(db: Session, *, report: Report) -> Path:
    asset = None
    if report.asset_id:
        asset = db.query(Asset).filter(Asset.id == report.asset_id).first()

    title = report.name
    if asset and asset.name not in title:
        title = f"{title} — {asset.name}"

    pdf_bytes = build_text_pdf(title=title, lines=_report_lines(db, report=report, asset=asset))
    path = report_file_path(report.id)
    path.write_bytes(pdf_bytes)
    return path
