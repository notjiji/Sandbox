from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure, task_postrun, task_prerun, worker_process_init

from app.core.config import get_settings
from app.core.logging import get_logger, log_context, setup_logging

settings = get_settings()

celery_app = Celery(
    "sandbox",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.jobs.example", "app.jobs.scans", "app.jobs.reports", "app.jobs.monitoring"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
    beat_schedule={
        "heartbeat": {
            "task": "app.jobs.example.heartbeat",
            "schedule": crontab(minute="*/5"),
        },
        "check-scan-schedules": {
            "task": "app.jobs.scans.check_due_schedules",
            "schedule": crontab(minute="*"),
        },
        "reconcile-offline-agents": {
            "task": "app.jobs.monitoring.reconcile_offline_agents",
            "schedule": crontab(minute="*/2"),
        },
    },
)

_task_log_context: dict[str, object] = {}


@worker_process_init.connect
def configure_worker_logging(**_kwargs) -> None:
    setup_logging(
        settings.LOG_LEVEL,
        service_name="sandbox-worker",
        environment=settings.ENVIRONMENT,
    )


@task_prerun.connect
def bind_task_log_context(task_id, task, *args, **kwargs) -> None:
    correlation_id = None
    if kwargs:
        correlation_id = kwargs.get("correlation_id")
    if correlation_id is None and task.request.headers:
        correlation_id = task.request.headers.get("correlation_id")

    ctx = log_context(
        request_id=task_id,
        correlation_id=correlation_id or task_id,
    )
    _task_log_context[task_id] = ctx
    ctx.__enter__()


@task_postrun.connect
def reset_task_log_context(task_id, **_kwargs) -> None:
    ctx = _task_log_context.pop(task_id, None)
    if ctx is not None:
        ctx.__exit__(None, None, None)


@task_failure.connect
def log_task_failure(
    task_id,
    exception,
    traceback,
    einfo,
    sender,
    **kwargs,
) -> None:
    logger = get_logger("sandbox.worker")
    logger.error(
        "celery task failed",
        extra={
            "task_name": sender.name if sender else None,
            "task_id": task_id,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "stack_trace": str(einfo) if einfo else traceback,
        },
        exc_info=einfo.exc_info if einfo else None,
    )
