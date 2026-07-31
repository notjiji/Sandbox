"""Notification orchestration service."""


class NotificationService:
    def notify_scan_completed(self, *, scan_id: str, organization_id: str) -> None:
        raise NotImplementedError("Notifications not implemented yet")
