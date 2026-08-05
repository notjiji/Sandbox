import uuid

from sqlalchemy.orm import Session

from app.assets.models import Asset
from app.audit.models import AuditLog
from app.reports.models import Report
from app.risk.models import AssetRisk
from app.scans.models import Scan


def list_asset_scans_for_timeline(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 50,
) -> list[Scan]:
    return (
        db.query(Scan)
        .filter(Scan.project_id == project_id, Scan.asset_id == asset_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )


def list_asset_risk_history(
    db: Session,
    *,
    asset_id: uuid.UUID,
    limit: int = 30,
) -> list[AssetRisk]:
    return (
        db.query(AssetRisk)
        .filter(AssetRisk.asset_id == asset_id)
        .order_by(AssetRisk.calculated_at.desc())
        .limit(limit)
        .all()
    )


def list_asset_audit_logs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 50,
) -> list[AuditLog]:
    from sqlalchemy import or_

    scan_ids = db.query(Scan.id).filter(
        Scan.project_id == project_id,
        Scan.asset_id == asset_id,
    )
    from app.findings.models import Finding

    finding_ids = db.query(Finding.id).filter(Finding.asset_id == asset_id)

    filters = or_(
        (AuditLog.resource_type == "asset") & (AuditLog.resource_id == asset_id),
        (AuditLog.resource_type == "scan") & AuditLog.resource_id.in_(scan_ids),
        (AuditLog.resource_type == "finding") & AuditLog.resource_id.in_(finding_ids),
    )

    return (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == organization_id, filters)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


def list_project_report_audit_logs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    limit: int = 20,
) -> list[AuditLog]:
    report_ids = db.query(Report.id).filter(Report.project_id == project_id)
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == organization_id,
            AuditLog.resource_type == "report",
            AuditLog.resource_id.in_(report_ids),
            AuditLog.action.in_(("report.create", "report.generate")),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
