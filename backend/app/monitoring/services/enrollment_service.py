import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationAppError
from app.core.security import generate_opaque_token, hash_token
from app.members.models import OrganizationMember
from app.monitoring.enums import (
    CREDENTIAL_PREFIX,
    ENROLLMENT_TOKEN_PREFIX,
    MONITORABLE_ASSET_TYPES,
    AgentStatus,
)
from app.monitoring.events import MonitoringAuditAction
from app.monitoring.repositories.agent_repository import (
    create_agent,
    get_agent_by_asset,
    get_agent_by_enrollment_hash,
)
from app.monitoring.schemas import AgentRegisterRequest, AgentRegisterResponse, EnrollmentResponse
from app.projects.validators import require_org_asset


def _issue_prefixed_token(prefix: str) -> tuple[str, str]:
    token = f"{prefix}{generate_opaque_token()}"
    return token, hash_token(token)


def _install_commands(api_url: str, enrollment_token: str) -> tuple[str, str]:
    install = (
        f"curl -fsSL {api_url}/monitoring/install.sh | "
        f"sudo env SANDBOX_API_URL={api_url} SANDBOX_ENROLLMENT_TOKEN={enrollment_token} bash"
    )
    python_cmd = (
        f"SANDBOX_API_URL={api_url} SANDBOX_ENROLLMENT_TOKEN={enrollment_token} python -m agent"
    )
    return install, python_cmd


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

    settings = get_settings()
    token, token_hash = _issue_prefixed_token(ENROLLMENT_TOKEN_PREFIX)
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.AGENT_ENROLLMENT_TOKEN_EXPIRE_MINUTES
    )
    agent = get_agent_by_asset(db, asset_id=asset.id)
    now = datetime.now(UTC)
    if agent is None:
        agent = create_agent(
            db,
            organization_id=membership.organization_id,
            project_id=project_id,
            asset_id=asset.id,
            enrollment_token_hash=token_hash,
            enrollment_expires_at=expires_at,
            created_by=membership.user_id,
        )
    else:
        if agent.status == AgentStatus.REVOKED:
            agent.status = AgentStatus.PENDING
            agent.revoked_at = None
            agent.credential_hash = None
        agent.enrollment_token_hash = token_hash
        agent.enrollment_expires_at = expires_at
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

    api_url = settings.PUBLIC_API_URL.rstrip("/")
    install_command, python_command = _install_commands(api_url, token)
    return EnrollmentResponse(
        agent_id=str(agent.id),
        asset_id=str(asset.id),
        enrollment_token=token,
        expires_at=expires_at,
        status=agent.status,
        install_command=install_command,
        python_command=python_command,
        api_url=api_url,
    )


def register_agent(db: Session, *, body: AgentRegisterRequest) -> AgentRegisterResponse:
    token = body.enrollment_token.strip()
    if not token.startswith(ENROLLMENT_TOKEN_PREFIX):
        raise UnauthorizedError("Invalid or expired enrollment token")

    agent = get_agent_by_enrollment_hash(db, enrollment_token_hash=hash_token(token))
    if agent is None or agent.status == AgentStatus.REVOKED:
        raise UnauthorizedError("Invalid or expired enrollment token")

    now = datetime.now(UTC)
    expires_at = agent.enrollment_expires_at
    if expires_at is None:
        raise UnauthorizedError("Invalid or expired enrollment token")
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < now:
        raise UnauthorizedError("Invalid or expired enrollment token")

    credential, credential_hash = _issue_prefixed_token(CREDENTIAL_PREFIX)
    agent.credential_hash = credential_hash
    agent.enrollment_token_hash = None
    agent.enrollment_expires_at = None
    agent.status = AgentStatus.ONLINE
    agent.last_seen_at = now
    if body.hostname:
        agent.hostname = body.hostname
    if body.agent_version:
        agent.agent_version = body.agent_version
    db.add(agent)
    record_audit_event(
        db,
        action=MonitoringAuditAction.REGISTER,
        user_id=None,
        organization_id=agent.organization_id,
        resource_type="monitoring_agent",
        resource_id=agent.id,
        details={"asset_id": str(agent.asset_id), "project_id": str(agent.project_id)},
    )
    db.commit()
    return AgentRegisterResponse(
        agent_id=str(agent.id),
        asset_id=str(agent.asset_id),
        credential=credential,
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
    agent.enrollment_token_hash = None
    agent.enrollment_expires_at = None
    agent.credential_hash = None
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
