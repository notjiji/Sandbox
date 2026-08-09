"""Access validation — AI never crosses organization boundaries."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.assets.repositories.asset_repository import get_asset_by_id_for_organization
from app.core.exceptions import NotFoundError, ValidationAppError
from app.findings.repositories.finding_repository import get_finding_by_id
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.scans.repositories.scan_repository import get_scan_for_asset
from app.services.ai.models import AICapability, AIChatRequest


def validate_chat_request(
    db: Session,
    membership: OrganizationMember,
    request: AIChatRequest,
) -> None:
    """Ensure referenced entities belong to the user's organization."""
    if request.project_id is not None:
        require_active_project(db, membership, request.project_id)

    if request.asset_id is not None:
        asset = get_asset_by_id_for_organization(
            db,
            organization_id=membership.organization_id,
            asset_id=request.asset_id,
        )
        if asset is None:
            raise NotFoundError("Asset")
        if request.project_id is not None and asset.project_id != request.project_id:
            raise NotFoundError("Asset")

    if request.scan_id is not None:
        if request.project_id is None or request.asset_id is None:
            raise ValidationAppError("scan_id requires project_id and asset_id")
        scan = get_scan_for_asset(
            db,
            project_id=request.project_id,
            asset_id=request.asset_id,
            scan_id=request.scan_id,
        )
        if scan is None:
            raise NotFoundError("Scan")

    if request.finding_id is not None:
        if request.project_id is None:
            raise ValidationAppError("finding_id requires project_id")
        finding = get_finding_by_id(db, project_id=request.project_id, finding_id=request.finding_id)
        if finding is None:
            raise NotFoundError("Finding")
        if request.asset_id is not None and finding.asset_id != request.asset_id:
            raise NotFoundError("Finding")

    _validate_capability_requirements(request)


def _validate_capability_requirements(request: AIChatRequest) -> None:
    capability = request.capability
    if capability in {AICapability.ASSET_SUMMARY, AICapability.COMPARE_SCANS} and request.asset_id is None:
        raise ValidationAppError(f"{capability.value} requires asset_id")
    if capability == AICapability.COMPARE_SCANS and request.project_id is None:
        raise ValidationAppError("compare_scans requires project_id")
    if capability in {AICapability.EXPLAIN_FINDING, AICapability.REMEDIATION}:
        if not request.finding_id and not request.finding_code:
            raise ValidationAppError(f"{capability.value} requires finding_id or finding_code")
