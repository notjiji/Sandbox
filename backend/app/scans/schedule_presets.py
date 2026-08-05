"""Per-asset scan schedule presets and next-run calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.scans.enums import SchedulePreset, ScanType


@dataclass(frozen=True)
class SchedulePresetConfig:
    label: str
    cadence: str
    scan_type: ScanType
    selected_plugins: list[str] | None


SCHEDULE_PRESET_ORDER: tuple[SchedulePreset, ...] = (
    SchedulePreset.QUICK_DAILY,
    SchedulePreset.FULL_SUNDAY,
    SchedulePreset.SSL_12H,
    SchedulePreset.DNS_WEEKLY,
)

SCHEDULE_PRESET_CONFIG: dict[SchedulePreset, SchedulePresetConfig] = {
    SchedulePreset.QUICK_DAILY: SchedulePresetConfig(
        label="Quick Scan",
        cadence="Daily",
        scan_type=ScanType.QUICK,
        selected_plugins=None,
    ),
    SchedulePreset.FULL_SUNDAY: SchedulePresetConfig(
        label="Full Scan",
        cadence="Sunday",
        scan_type=ScanType.FULL,
        selected_plugins=None,
    ),
    SchedulePreset.SSL_12H: SchedulePresetConfig(
        label="SSL",
        cadence="Every 12 hours",
        scan_type=ScanType.CUSTOM,
        selected_plugins=["ssl"],
    ),
    SchedulePreset.DNS_WEEKLY: SchedulePresetConfig(
        label="DNS",
        cadence="Weekly",
        scan_type=ScanType.CUSTOM,
        selected_plugins=["dns"],
    ),
}


def compute_next_run_at(
    preset: SchedulePreset,
    *,
    reference: datetime | None = None,
    last_run_at: datetime | None = None,
) -> datetime:
    now = reference or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    if preset == SchedulePreset.QUICK_DAILY:
        candidate = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    if preset == SchedulePreset.FULL_SUNDAY:
        days_ahead = (6 - now.weekday()) % 7
        candidate = (now + timedelta(days=days_ahead)).replace(
            hour=3, minute=0, second=0, microsecond=0
        )
        if candidate <= now:
            candidate += timedelta(days=7)
        return candidate

    if preset == SchedulePreset.SSL_12H:
        if last_run_at is not None:
            anchor = last_run_at if last_run_at.tzinfo else last_run_at.replace(tzinfo=UTC)
            return anchor + timedelta(hours=12)
        hour = 0 if now.hour < 12 else 12
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(hours=12)
        return candidate

    if preset == SchedulePreset.DNS_WEEKLY:
        if last_run_at is not None:
            anchor = last_run_at if last_run_at.tzinfo else last_run_at.replace(tzinfo=UTC)
            return anchor + timedelta(days=7)
        days_ahead = (0 - now.weekday()) % 7
        candidate = (now + timedelta(days=days_ahead)).replace(
            hour=4, minute=0, second=0, microsecond=0
        )
        if candidate <= now:
            candidate += timedelta(days=7)
        return candidate

    raise ValueError(f"Unknown schedule preset: {preset}")
