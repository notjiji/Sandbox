"""Notification subscriber — reserved for email/websocket delivery."""

from __future__ import annotations

from app.core.logging import get_logger
from app.events.bus import DomainEvent

logger = get_logger("sandbox.notifications")

_NOTIFY_ACTIONS = {
    "scan.completed",
    "scan.failed",
    "org.member_invite",
    "report.generate",
    "monitoring.alert_opened",
}


def on_domain_event(event: DomainEvent) -> None:
    if event.name not in _NOTIFY_ACTIONS:
        return
    logger.info(
        "notification hook",
        extra={
            "event": event.name,
            "organization_id": str(event.organization_id) if event.organization_id else None,
        },
    )
