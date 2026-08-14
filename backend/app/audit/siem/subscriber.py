"""Forward persisted audit events to the configured SIEM sink."""

from __future__ import annotations

from app.audit.siem import build_siem_payload, get_siem_sink
from app.core.logging import get_logger
from app.events.bus import DomainEvent

logger = get_logger("sandbox.audit.siem")


def forward_audit_to_siem(event: DomainEvent) -> None:
    record = event.record
    if record is None:
        return
    sink = get_siem_sink()
    if sink is None:
        return
    try:
        sink.send(build_siem_payload(record))
    except Exception:
        logger.exception(
            "SIEM export failed",
            extra={"action": getattr(record, "action", event.name)},
        )
