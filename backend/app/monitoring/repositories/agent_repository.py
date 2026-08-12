import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.monitoring.enums import AGENT_OFFLINE_SECONDS, AgentStatus
from app.monitoring.models import MonitoringAgent


def get_agent_by_asset(db: Session, *, asset_id: uuid.UUID) -> MonitoringAgent | None:
    return db.query(MonitoringAgent).filter(MonitoringAgent.asset_id == asset_id).first()


def get_agent_by_credential_hash(db: Session, *, credential_hash: str) -> MonitoringAgent | None:
    return (
        db.query(MonitoringAgent)
        .filter(MonitoringAgent.credential_hash == credential_hash)
        .first()
    )


def get_agent_by_enrollment_hash(db: Session, *, enrollment_token_hash: str) -> MonitoringAgent | None:
    return (
        db.query(MonitoringAgent)
        .filter(MonitoringAgent.enrollment_token_hash == enrollment_token_hash)
        .first()
    )


def get_agent_by_id(db: Session, *, agent_id: uuid.UUID) -> MonitoringAgent | None:
    return db.query(MonitoringAgent).filter(MonitoringAgent.id == agent_id).first()


def list_agents_for_organization(db: Session, *, organization_id: uuid.UUID) -> list[MonitoringAgent]:
    return (
        db.query(MonitoringAgent)
        .filter(
            MonitoringAgent.organization_id == organization_id,
            MonitoringAgent.status != AgentStatus.REVOKED,
        )
        .order_by(MonitoringAgent.updated_at.desc())
        .all()
    )


def create_agent(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    enrollment_token_hash: str,
    enrollment_expires_at: datetime,
    created_by: uuid.UUID | None,
) -> MonitoringAgent:
    agent = MonitoringAgent(
        organization_id=organization_id,
        project_id=project_id,
        asset_id=asset_id,
        enrollment_token_hash=enrollment_token_hash,
        enrollment_expires_at=enrollment_expires_at,
        status=AgentStatus.PENDING,
        created_by=created_by,
        enrolled_at=datetime.now(UTC),
    )
    db.add(agent)
    db.flush()
    return agent


def effective_status(agent: MonitoringAgent, *, now: datetime | None = None) -> AgentStatus:
    if agent.status in {AgentStatus.REVOKED, AgentStatus.PENDING}:
        return agent.status
    if agent.last_seen_at is None:
        return AgentStatus.OFFLINE
    current = now or datetime.now(UTC)
    last_seen = agent.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=UTC)
    if (current - last_seen).total_seconds() > AGENT_OFFLINE_SECONDS:
        return AgentStatus.OFFLINE
    return AgentStatus.ONLINE
