import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.finding import Finding
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.repositories.finding import get_finding_by_id, list_findings_for_project, update_finding
from app.repositories.project import get_project_by_id
from app.schemas.finding import FindingListResponse, FindingSummary, UpdateFindingRequest
from app.services.audit import AuditAction, record_audit_event


def _get_active_project(
    db: Session,
    membership: OrganizationMember,
    project_id: uuid.UUID,
) -> Project:
    project = get_project_by_id(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
    )
    if not project or not project.is_active:
        raise NotFoundError("Project")
    return project


def _to_finding_summary(finding: Finding) -> FindingSummary:
    return FindingSummary(
        id=str(finding.id),
        project_id=str(finding.project_id),
        scan_id=str(finding.scan_id),
        asset_id=str(finding.asset_id),
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        status=finding.status,
    )


def list_project_findings(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> FindingListResponse:
    _get_active_project(db, membership, project_id)
    findings = list_findings_for_project(db, project_id=project_id)
    items = [_to_finding_summary(finding) for finding in findings]
    return FindingListResponse(items=items, total=len(items))


def get_project_finding(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
) -> FindingSummary:
    _get_active_project(db, membership, project_id)
    finding = get_finding_by_id(db, project_id=project_id, finding_id=finding_id)
    if not finding:
        raise NotFoundError("Finding")
    return _to_finding_summary(finding)


def update_project_finding(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: UpdateFindingRequest,
) -> FindingSummary:
    _get_active_project(db, membership, project_id)
    finding = get_finding_by_id(db, project_id=project_id, finding_id=finding_id)
    if not finding:
        raise NotFoundError("Finding")
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")

    update_finding(
        db,
        finding,
        title=body.title,
        description=body.description,
        severity=body.severity,
        status=body.status,
    )
    action = (
        AuditAction.FINDING_REVIEW
        if body.status is not None
        else AuditAction.FINDING_UPDATE
    )
    record_audit_event(
        db,
        action=action,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="finding",
        resource_id=finding.id,
        details=body.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(finding)
    return _to_finding_summary(finding)
