"""Schedules background jobs via Celery."""


class SchedulerService:
    def enqueue_scan(self, *, scan_id: str) -> str:
        raise NotImplementedError("Job scheduling not implemented yet")

    def enqueue_report(self, *, report_id: str) -> str:
        raise NotImplementedError("Job scheduling not implemented yet")
