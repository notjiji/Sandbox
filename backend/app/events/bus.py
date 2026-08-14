"""In-process domain event bus.

Feature modules publish once. Subscribers (audit, SIEM, notifications, future
webhooks/analytics) run independently. A failing subscriber never blocks others
or the business action.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.events.names import normalize_action

logger = get_logger("sandbox.events")

Handler = Callable[["DomainEvent"], None]


@dataclass
class DomainEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    db: Session | None = None
    organization_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | str | None = None
    resource_type: str | None = None
    resource_id: uuid.UUID | str | None = None
    severity: str | None = None
    record: Any = None


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[Handler] = []
        self._ready = False

    def subscribe(self, handler: Handler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    def publish(self, name: str, payload: dict[str, Any] | None = None, **kwargs: Any) -> DomainEvent:
        ensure_default_handlers()
        event = DomainEvent(
            name=normalize_action(name) or name,
            payload=dict(payload or {}),
            **kwargs,
        )
        for handler in list(self._handlers):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "event handler failed",
                    extra={
                        "event": event.name,
                        "handler": getattr(handler, "__qualname__", repr(handler)),
                    },
                )
        return event


event_bus = EventBus()


def ensure_default_handlers() -> None:
    if event_bus._ready:
        return
    from app.audit.siem.subscriber import forward_audit_to_siem
    from app.audit.subscriber import persist_audit_event
    from app.notifications.subscriber import on_domain_event

    event_bus.subscribe(persist_audit_event)
    event_bus.subscribe(forward_audit_to_siem)
    event_bus.subscribe(on_domain_event)
    event_bus._ready = True
