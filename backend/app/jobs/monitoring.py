"""Expire stale monitoring agents and open SERVER_OFFLINE alerts."""

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.monitoring.enums import AgentStatus
from app.monitoring.models import MonitoringAgent
from app.monitoring.services.alert_service import reconcile_offline_agents
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.jobs.monitoring")


@celery_app.task(name="app.jobs.monitoring.reconcile_offline_agents")
def reconcile_offline_agents_task() -> int:
    db = SessionLocal()
    try:
        agents = (
            db.query(MonitoringAgent)
            .filter(MonitoringAgent.status.notin_((AgentStatus.REVOKED, AgentStatus.PENDING)))
            .all()
        )
        opened = reconcile_offline_agents(db, agents)
        db.commit()
        if opened:
            logger.info("opened server-offline alerts", extra={"opened": opened})
        return opened
    except Exception:
        db.rollback()
        logger.exception("offline agent reconcile failed")
        raise
    finally:
        db.close()
