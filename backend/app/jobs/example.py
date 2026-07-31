from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.jobs")


@celery_app.task(name="app.jobs.example.heartbeat")
def heartbeat() -> str:
    logger.info("celery heartbeat")
    return "ok"
