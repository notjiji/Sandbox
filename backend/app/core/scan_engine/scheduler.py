"""Schedules scan jobs (delegates to core.scheduler)."""


class ScanScheduler:
    def enqueue(self, *, scan_id: str) -> str:
        raise NotImplementedError("Scan scheduling not implemented yet")
