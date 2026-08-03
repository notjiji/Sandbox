"""Scan lifecycle state machine and transition timestamps."""

from datetime import UTC, datetime

from app.core.exceptions import ValidationAppError
from app.scans.enums import ScanStatus
from app.scans.models import Scan

# Allowed status transitions
VALID_TRANSITIONS: dict[ScanStatus, set[ScanStatus]] = {
    ScanStatus.PENDING: {ScanStatus.QUEUED, ScanStatus.CANCELLED},
    ScanStatus.QUEUED: {ScanStatus.RUNNING, ScanStatus.CANCELLED},
    ScanStatus.RUNNING: {ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED},
    ScanStatus.FAILED: {ScanStatus.QUEUED},
    ScanStatus.COMPLETED: set(),
    ScanStatus.CANCELLED: set(),
}

STATUS_TIMESTAMP_ATTR: dict[ScanStatus, str] = {
    ScanStatus.PENDING: "pending_at",
    ScanStatus.QUEUED: "queued_at",
    ScanStatus.RUNNING: "running_at",
    ScanStatus.COMPLETED: "completed_at",
    ScanStatus.FAILED: "failed_at",
    ScanStatus.CANCELLED: "cancelled_at",
}


def can_transition(current: ScanStatus, target: ScanStatus) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


def transition_scan_status(scan: Scan, *, status: ScanStatus, at: datetime | None = None) -> Scan:
    """Move a scan to a new lifecycle state and stamp the transition time."""
    if scan.status == status:
        return scan

    if not can_transition(scan.status, status):
        raise ValidationAppError(
            f"Cannot transition scan from {scan.status.value} to {status.value}"
        )

    timestamp = at or datetime.now(UTC)
    scan.status = status
    setattr(scan, STATUS_TIMESTAMP_ATTR[status], timestamp)
    return scan


def lifecycle_timestamps(scan: Scan) -> dict[str, datetime | None]:
    return {
        "pending_at": scan.pending_at,
        "queued_at": scan.queued_at,
        "running_at": scan.running_at,
        "completed_at": scan.completed_at,
        "failed_at": scan.failed_at,
        "cancelled_at": scan.cancelled_at,
    }
