from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure, task_postrun, task_prerun, worker_process_init

from app.core.config import get_settings
from app.core.logging import get_logger, log_context, setup_logging
from app.workers.job_failures import log_failed_job, recover_failed_job_state

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
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=86400,
    task_annotations={
        "app.jobs.scans.execute_scan": {
            "soft_time_limit": settings.SCAN_TASK_SOFT_TIMEOUT_SECONDS,
            "time_limit": settings.SCAN_TASK_HARD_TIMEOUT_SECONDS,
            "acks_late": True,
            "reject_on_worker_lost": True,
        },
        "app.jobs.reports.generate_report": {
            "soft_time_limit": settings.REPORT_TASK_SOFT_TIMEOUT_SECONDS,
            "time_limit": settings.REPORT_TASK_HARD_TIMEOUT_SECONDS,
            "acks_late": True,
            "reject_on_worker_lost": True,
        },
    },
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
            "schedule": crontab(minute="*"),
        },
        "reconcile-stale-jobs": {
            "task": "app.jobs.scans.reconcile_stale_jobs",
            "schedule": crontab(minute="*/5"),
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
def handle_task_failure(
    task_id,
    exception,
    args,
    kwargs,
    traceback,
    einfo,
    sender,
    **_,
) -> None:
    task_name = sender.name if sender else None
    log_failed_job(
        task_id=task_id,
        task_name=task_name,
        exception=exception,
        traceback=traceback,
        einfo=einfo,
    )
    recover_failed_job_state(
        task_name=task_name,
        kwargs=kwargs or {},
        exception=exception,
    )
