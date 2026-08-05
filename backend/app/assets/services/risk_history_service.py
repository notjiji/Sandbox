"""Asset risk history — trend, deltas, and finding-level explanations."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.assets.repositories.timeline_repository import list_asset_risk_history
from app.assets.schemas_risk_history import (
    AssetRiskHistoryResponse,
    RiskChangeExplanation,
    RiskHistoryChange,
    RiskHistoryPoint,
)
from app.assets.services.overview_service import _asset_risk_response
from app.core.exceptions import NotFoundError
from app.findings.repositories.finding_repository import list_finding_changes_between
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.assets.repositories.asset_repository import get_asset_by_id


def _explain_change(
    db: Session,
    *,
    asset_id: uuid.UUID,
    previous,
    current,
) -> list[RiskChangeExplanation]:
    since = previous.calculated_at
    until = current.calculated_at
    if since >= until:
        return []

    new_findings, resolved_findings = list_finding_changes_between(
        db,
        asset_id=asset_id,
        since=since,
        until=until,
    )

    resolved_ids = {finding.id for finding in resolved_findings}
    explanations: list[RiskChangeExplanation] = []

    for finding in new_findings:
        if finding.id in resolved_ids:
            continue
        explanations.append(
            RiskChangeExplanation(
                delta=float(finding.risk_score),
                title=finding.title,
                kind="new",
                finding_id=str(finding.id),
                severity=finding.severity.value,
            )
        )

    for finding in resolved_findings:
        suffix = " fixed" if not finding.title.lower().endswith("fixed") else ""
        explanations.append(
            RiskChangeExplanation(
                delta=-float(finding.risk_score),
                title=f"{finding.title}{suffix}",
                kind="resolved",
                finding_id=str(finding.id),
                severity=finding.severity.value,
            )
        )

    explanations.sort(key=lambda item: abs(item.delta), reverse=True)
    return explanations


def get_asset_risk_history(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 20,
) -> AssetRiskHistoryResponse:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(
        db,
        project_id=project_id,
        asset_id=asset_id,
        include_deleted=True,
    )
    if not asset:
        raise NotFoundError("Asset")

    rows = list(reversed(list_asset_risk_history(db, asset_id=asset_id, limit=limit)))
    current = _asset_risk_response(
        db,
        organization_id=membership.organization_id,
        asset_id=asset_id,
    )

    trend: list[RiskHistoryPoint] = []
    changes: list[RiskHistoryChange] = []

    for index, row in enumerate(rows):
        previous = rows[index - 1] if index > 0 else None
        score_delta = None if previous is None else float(row.score) - float(previous.score)
        total_risk_delta = None if previous is None else float(row.total_risk) - float(previous.total_risk)

        trend.append(
            RiskHistoryPoint(
                id=str(row.id),
                date=row.calculated_at,
                security_score=float(row.score),
                total_risk=float(row.total_risk),
                grade=row.grade,
                scan_id=str(row.scan_id) if row.scan_id else None,
                score_delta=score_delta,
                total_risk_delta=total_risk_delta,
            )
        )

        if previous is not None:
            explanations = _explain_change(
                db,
                asset_id=asset_id,
                previous=previous,
                current=row,
            )
            changes.append(
                RiskHistoryChange(
                    from_score=float(previous.score),
                    to_score=float(row.score),
                    from_date=previous.calculated_at,
                    to_date=row.calculated_at,
                    score_delta=float(row.score) - float(previous.score),
                    total_risk_delta=float(row.total_risk) - float(previous.total_risk),
                    explanations=explanations,
                )
            )

    changes.reverse()
    latest_change = changes[0] if changes else None

    return AssetRiskHistoryResponse(
        current=current,
        trend=trend,
        latest_change=latest_change,
        changes=changes,
    )
