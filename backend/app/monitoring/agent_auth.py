from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import hash_token
from app.monitoring.enums import AgentStatus
from app.monitoring.models import MonitoringAgent
from app.monitoring.repositories.agent_repository import get_agent_by_credential_hash


def get_current_agent(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
) -> MonitoringAgent:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Agent credential required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise UnauthorizedError("Agent credential required")
    agent = get_agent_by_credential_hash(db, credential_hash=hash_token(token))
    if agent is None or agent.status == AgentStatus.REVOKED or agent.credential_hash is None:
        raise UnauthorizedError("Invalid or revoked agent credential")
    return agent
