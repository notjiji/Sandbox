"""Build minimal structured context for the LLM from database scan results."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.findings.repositories.finding_repository import get_finding_by_id
from app.members.models import OrganizationMember
from app.services.ai import tools
from app.services.ai.models import AIChatRequest, AIContextBundle, AICapability


class ContextBuilder:
    """Loads only the data relevant to the user's question."""

    def build(
        self,
        db: Session,
        membership: OrganizationMember,
        request: AIChatRequest,
    ) -> AIContextBundle:
        org_id = membership.organization_id
        bundle = AIContextBundle(
            organization_id=str(org_id),
            capability=request.capability.value,
        )

        if request.capability == AICapability.ORGANIZATION_OVERVIEW:
            bundle.organization_summary = tools.get_organization_summary(db, organization_id=org_id)
            return bundle

        asset = None
        if request.asset_id is not None:
            asset = tools.get_asset(db, organization_id=org_id, asset_id=request.asset_id)
            if asset is not None:
                bundle.asset = tools.build_asset_snapshot(db, organization_id=org_id, asset=asset)
                bundle.risk_score = bundle.asset.risk_score

        if request.project_id is not None and request.scan_id is not None:
            bundle.findings = tools.get_findings_for_scan(
                db,
                project_id=request.project_id,
                scan_id=request.scan_id,
            )
            bundle.scan = next(
                (item for item in tools.get_scan_history(db, project_id=request.project_id, asset_id=request.asset_id) if item.scan_id == str(request.scan_id)),
                None,
            ) if request.asset_id else None
        elif asset is not None and request.project_id is not None:
            latest = tools.get_latest_scan(db, project_id=request.project_id, asset_id=asset.id)
            bundle.scan = latest
            if latest is not None:
                bundle.findings = tools.get_findings_for_scan(
                    db,
                    project_id=request.project_id,
                    scan_id=uuid.UUID(latest.scan_id),
                )

        if request.finding_id and request.project_id:
            finding = get_finding_by_id(db, project_id=request.project_id, finding_id=request.finding_id)
            if finding is not None:
                from app.services.ai.tools import _finding_to_context

                bundle.findings = [_finding_to_context(finding)]
        elif request.finding_code:
            matches = tools.search_findings(db, organization_id=org_id, keyword=request.finding_code, limit=5)
            bundle.findings = [item for item in matches if item.finding_code == request.finding_code] or matches[:1]

        if request.capability == AICapability.COMPARE_SCANS and request.project_id and request.asset_id:
            bundle.scan_comparison = tools.compare_latest_scans(
                db,
                project_id=request.project_id,
                asset_id=request.asset_id,
            )

        if request.capability in {AICapability.EXECUTIVE_SUMMARY, AICapability.TECHNICAL_SUMMARY}:
            bundle.organization_summary = tools.get_organization_summary(db, organization_id=org_id)

        if request.message and request.capability == AICapability.GENERAL and not bundle.findings:
            keyword = request.finding_code or request.message.split()[0]
            if len(keyword) >= 3:
                bundle.findings = tools.search_findings(db, organization_id=org_id, keyword=keyword, limit=10)

        bundle.metadata = {
            "audience": request.audience,
            "user_message": request.message,
        }
        return bundle
