"""Domain event bus."""

from app.events.bus import DomainEvent, event_bus, ensure_default_handlers

__all__ = ["DomainEvent", "event_bus", "ensure_default_handlers"]
