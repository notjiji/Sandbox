from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.tasks")


@celery_app.task(name="app.tasks.example.heartbeat")
def heartbeat() -> str:
    logger.info("celery heartbeat")
    return "ok"
