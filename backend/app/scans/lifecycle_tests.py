"""Scan lifecycle transition tests."""


def test_valid_scan_transitions() -> None:
    from app.scans.enums import ScanStatus
    from app.scans.lifecycle import can_transition

    assert can_transition(ScanStatus.PENDING, ScanStatus.QUEUED)
    assert can_transition(ScanStatus.QUEUED, ScanStatus.RUNNING)
    assert can_transition(ScanStatus.RUNNING, ScanStatus.COMPLETED)
    assert can_transition(ScanStatus.RUNNING, ScanStatus.FAILED)
    assert can_transition(ScanStatus.RUNNING, ScanStatus.CANCELLED)
    assert can_transition(ScanStatus.FAILED, ScanStatus.QUEUED)
    assert not can_transition(ScanStatus.COMPLETED, ScanStatus.RUNNING)
    assert not can_transition(ScanStatus.PENDING, ScanStatus.RUNNING)


def test_transition_sets_timestamp() -> None:
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from app.scans.enums import ScanStatus
    from app.scans.lifecycle import transition_scan_status

    scan = SimpleNamespace(
        status=ScanStatus.PENDING,
        pending_at=datetime.now(UTC),
        queued_at=None,
        running_at=None,
        completed_at=None,
        failed_at=None,
        cancelled_at=None,
    )
    when = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    transition_scan_status(scan, status=ScanStatus.QUEUED, at=when)
    assert scan.status == ScanStatus.QUEUED
    assert scan.queued_at == when


def test_invalid_transition_raises() -> None:
    from types import SimpleNamespace

    from app.core.exceptions import ValidationAppError
    from app.scans.enums import ScanStatus
    from app.scans.lifecycle import transition_scan_status

    scan = SimpleNamespace(status=ScanStatus.COMPLETED)
    try:
        transition_scan_status(scan, status=ScanStatus.RUNNING)
        raised = False
    except ValidationAppError:
        raised = True
    assert raised
