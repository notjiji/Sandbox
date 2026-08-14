"""Shared scan audit writes for executor and orchestrator."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.models import Asset
from app.audit.service import record_audit_event
from app.projects.models import Project
from app.scans.models import Scan


def record_scan_audit(
    db: Session,
    scan: Scan,
    *,
    action: str,
    extra: dict | None = None,
    user_id: uuid.UUID | None = None,
) -> None:
    project = db.query(Project).filter(Project.id == scan.project_id).first()
    asset = db.query(Asset).filter(Asset.id == scan.asset_id).first()
    details: dict = {
        "project_id": str(scan.project_id),
        "asset_id": str(scan.asset_id),
        "status": scan.status.value if hasattr(scan.status, "value") else str(scan.status),
    }
    if asset is not None:
        details["asset_name"] = asset.name
        details["asset_type"] = asset.type.value if hasattr(asset.type, "value") else str(asset.type)
    if extra:
        details.update(extra)
    record_audit_event(
        db,
        action=action,
        user_id=user_id if user_id is not None else scan.created_by,
        organization_id=project.organization_id if project else None,
        resource_type="scan",
        resource_id=scan.id,
        details=details,
    )
