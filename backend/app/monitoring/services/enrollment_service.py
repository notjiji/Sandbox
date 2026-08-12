import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.security import generate_opaque_token, hash_token
from app.members.models import OrganizationMember
from app.monitoring.enums import AGENT_TOKEN_PREFIX, MONITORABLE_ASSET_TYPES, AgentStatus
from app.monitoring.events import MonitoringAuditAction
from app.monitoring.repositories.agent_repository import create_agent, get_agent_by_asset
from app.monitoring.schemas import EnrollmentResponse
from app.projects.validators import require_org_asset


def _issue_token() -> tuple[str, str]:
    token = f"{AGENT_TOKEN_PREFIX}{generate_opaque_token()}"
    return token, hash_token(token)


def enroll_agent(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> EnrollmentResponse:
    asset = require_org_asset(db, membership, project_id=project_id, asset_id=asset_id)
    if asset.type not in MONITORABLE_ASSET_TYPES:
        raise ValidationAppError("Monitoring agents can only be enrolled on server assets")

    token, token_hash = _issue_token()
    agent = get_agent_by_asset(db, asset_id=asset.id)
    now = datetime.now(UTC)
    if agent is None:
        agent = create_agent(
            db,
            organization_id=membership.organization_id,
            project_id=project_id,
            asset_id=asset.id,
            token_hash=token_hash,
            created_by=membership.user_id,
        )
    else:
        agent.token_hash = token_hash
        agent.status = AgentStatus.PENDING
        agent.revoked_at = None
        agent.enrolled_at = now
        db.add(agent)

    record_audit_event(
        db,
        action=MonitoringAuditAction.ENROLL,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="monitoring_agent",
        resource_id=agent.id,
        details={"asset_id": str(asset.id), "project_id": str(project_id)},
    )
    db.commit()
    db.refresh(agent)

    api_url = get_settings().PUBLIC_API_URL.rstrip("/")
    install_command = (
        f"SANDBOX_API_URL={api_url} SANDBOX_AGENT_TOKEN={token} python -m sandbox_agent"
    )
    return EnrollmentResponse(
        agent_id=str(agent.id),
        asset_id=str(asset.id),
        token=token,
        status=agent.status,
        install_command=install_command,
        api_url=api_url,
    )


def revoke_agent(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    require_org_asset(db, membership, project_id=project_id, asset_id=asset_id)
    agent = get_agent_by_asset(db, asset_id=asset_id)
    if agent is None:
        raise NotFoundError("Monitoring agent")
    agent.status = AgentStatus.REVOKED
    agent.revoked_at = datetime.now(UTC)
    agent.token_hash = hash_token(f"revoked-{uuid.uuid4()}")
    db.add(agent)
    record_audit_event(
        db,
        action=MonitoringAuditAction.REVOKE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="monitoring_agent",
        resource_id=agent.id,
        details={"asset_id": str(asset_id), "project_id": str(project_id)},
    )
    db.commit()
