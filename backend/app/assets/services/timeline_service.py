"""Unified asset timeline — scans, reports, risk, updates in one feed."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.assets.repositories.asset_repository import get_asset_by_id
from app.assets.repositories.timeline_repository import (
    list_asset_audit_logs,
    list_asset_risk_history,
    list_asset_scans_for_timeline,
    list_project_report_audit_logs,
)
from app.assets.schemas_timeline import AssetTimelineResponse
from app.core.exceptions import NotFoundError
from app.members.models import OrganizationMember
from app.organizations.schemas_activity import ActivityEvent
from app.organizations.services.activity_service import present_activity_events
from app.projects.validators import require_active_project
from app.scans.enums import ScanStatus


def _scan_message(scan) -> str | None:
    if scan.status == ScanStatus.COMPLETED and scan.completed_at:
        return f"{scan.scan_type.value.replace('_', ' ').title()} scan completed"
    if scan.status == ScanStatus.FAILED and scan.failed_at:
        return f"{scan.scan_type.value.replace('_', ' ').title()} scan failed"
    if scan.status == ScanStatus.CANCELLED and scan.cancelled_at:
        return f"{scan.scan_type.value.replace('_', ' ').title()} scan cancelled"
    if scan.status == ScanStatus.RUNNING and scan.running_at:
        return f"{scan.scan_type.value.replace('_', ' ').title()} scan started"
    return None


def _scan_timestamp(scan) -> datetime | None:
    if scan.status == ScanStatus.COMPLETED:
        return scan.completed_at or scan.created_at
    if scan.status == ScanStatus.FAILED:
        return scan.failed_at or scan.created_at
    if scan.status == ScanStatus.CANCELLED:
        return scan.cancelled_at or scan.created_at
    if scan.status == ScanStatus.RUNNING:
        return scan.running_at or scan.created_at
    return scan.created_at


def _risk_events(
    rows: list,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> list[ActivityEvent]:
    if not rows:
        return []

    chronological = list(reversed(rows))
    events: list[ActivityEvent] = []
    for index, row in enumerate(chronological):
        if index == 0:
            events.append(
                ActivityEvent(
                    id=f"risk-{row.id}",
                    message=f"Risk score calculated at {row.score:.1f} (grade {row.grade})",
                    category="security",
                    action="asset.risk_calculated",
                    resource_type="asset",
                    resource_id=str(asset_id),
                    href=f"/projects/{project_id}/assets/{asset_id}",
                    created_at=row.calculated_at,
                )
            )
            continue

        previous = chronological[index - 1]
        delta = float(row.score) - float(previous.score)
        if abs(delta) < 0.1:
            continue

        if delta > 0:
            direction = "increased"
        else:
            direction = "decreased"

        events.append(
            ActivityEvent(
                id=f"risk-change-{row.id}",
                message=(
                    f"Risk score {direction} from {previous.score:.1f} to {row.score:.1f} "
                    f"(grade {previous.grade} → {row.grade})"
                ),
                category="security",
                action="asset.risk_changed",
                resource_type="asset",
                resource_id=str(asset_id),
                href=f"/projects/{project_id}/assets/{asset_id}",
                created_at=row.calculated_at,
            )
        )
    return events


def _with_project_hrefs(
    events: list[ActivityEvent],
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> list[ActivityEvent]:
    patched: list[ActivityEvent] = []
    for event in events:
        href = event.href
        if event.category == "scans":
            href = f"/projects/{project_id}/assets/{asset_id}/scans"
        elif event.category == "assets" and event.resource_id == str(asset_id):
            href = f"/projects/{project_id}/assets/{asset_id}"
        elif event.category == "findings":
            href = f"/projects/{project_id}/findings"
        elif event.category == "reports":
            href = f"/projects/{project_id}/reports"
        patched.append(event.model_copy(update={"href": href}))
    return patched


def get_asset_timeline(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 50,
) -> AssetTimelineResponse:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(
        db,
        project_id=project_id,
        asset_id=asset_id,
        include_deleted=True,
    )
    if not asset:
        raise NotFoundError("Asset")

    events: list[ActivityEvent] = []

    events.append(
        ActivityEvent(
            id=f"asset-created-{asset.id}",
            message=f"Asset {asset.name} created",
            category="assets",
            action="asset.create",
            resource_type="asset",
            resource_id=str(asset.id),
            href=f"/projects/{project_id}/assets/{asset_id}",
            created_at=asset.created_at,
        )
    )

    audit_records = list_asset_audit_logs(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
        asset_id=asset_id,
        limit=limit,
    )
    events.extend(
        _with_project_hrefs(
            present_activity_events(db, audit_records),
            project_id=project_id,
            asset_id=asset_id,
        )
    )

    report_records = list_project_report_audit_logs(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
        limit=20,
    )
    events.extend(
        _with_project_hrefs(
            present_activity_events(db, report_records),
            project_id=project_id,
            asset_id=asset_id,
        )
    )

    for scan in list_asset_scans_for_timeline(
        db, project_id=project_id, asset_id=asset_id, limit=limit
    ):
        message = _scan_message(scan)
        timestamp = _scan_timestamp(scan)
        if not message or not timestamp:
            continue
        events.append(
            ActivityEvent(
                id=f"scan-status-{scan.id}-{scan.status.value}",
                message=message,
                category="scans",
                action=f"scan.{scan.status.value}",
                resource_type="scan",
                resource_id=str(scan.id),
                href=f"/projects/{project_id}/assets/{asset_id}/scans",
                created_at=timestamp,
            )
        )

    events.extend(
        _risk_events(
            list_asset_risk_history(db, asset_id=asset_id),
            project_id=project_id,
            asset_id=asset_id,
        )
    )

    # Deduplicate by id, sort newest first
    seen: set[str] = set()
    unique: list[ActivityEvent] = []
    for event in sorted(events, key=lambda item: item.created_at, reverse=True):
        if event.id in seen:
            continue
        seen.add(event.id)
        unique.append(event)

    items = unique[:limit]
    return AssetTimelineResponse(items=items, total=len(unique))
