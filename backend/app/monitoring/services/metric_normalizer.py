"""Flatten collector payloads into (metric_type, value, unit) rows."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.monitoring.metric_types import (
    CPU_CORES,
    CPU_USAGE,
    DISK_AVAILABLE,
    DISK_TOTAL,
    DISK_USAGE,
    DISK_USED,
    LOAD_AVERAGE,
    MEMORY_AVAILABLE,
    MEMORY_TOTAL,
    MEMORY_USAGE,
    MEMORY_USED,
    PROCESS_COUNT,
    ROOT_FILESYSTEMS,
    UNIT_COUNT,
    UNIT_GB,
    UNIT_MB,
    UNIT_PERCENT,
    UNIT_RATIO,
    UNIT_SECONDS,
    UPTIME,
)
from app.monitoring.schemas import DiskFilesystem, MetricsPayload


@dataclass(frozen=True)
class MetricPoint:
    metric_type: str
    value: float
    unit: str
    labels: dict | None = field(default=None)


def _point(metric_type: str, value: float | int | None, unit: str, **labels: str) -> MetricPoint | None:
    if value is None:
        return None
    return MetricPoint(
        metric_type=metric_type,
        value=float(value),
        unit=unit,
        labels=labels or None,
    )


def _cpu_usage(metrics: MetricsPayload) -> float | None:
    return metrics.cpu_usage if metrics.cpu_usage is not None else metrics.cpu_percent


def _memory_usage(metrics: MetricsPayload) -> float | None:
    return metrics.usage_percent if metrics.usage_percent is not None else metrics.ram_percent


def _memory_used(metrics: MetricsPayload) -> float | None:
    return metrics.used_mb if metrics.used_mb is not None else metrics.ram_used_mb


def _memory_total(metrics: MetricsPayload) -> float | None:
    return metrics.total_mb if metrics.total_mb is not None else metrics.ram_total_mb


def _load_1m(metrics: MetricsPayload) -> float | None:
    if metrics.load_1m is not None:
        return metrics.load_1m
    if metrics.load_avg:
        return metrics.load_avg[0]
    return None


def _primary_disk(metrics: MetricsPayload) -> DiskFilesystem | None:
    if metrics.disks:
        root = next((item for item in metrics.disks if item.filesystem in ROOT_FILESYSTEMS), None)
        if root:
            return root
        with_usage = [item for item in metrics.disks if item.usage_percent is not None]
        if with_usage:
            return max(with_usage, key=lambda item: item.usage_percent or 0)
        return metrics.disks[0]
    if any(v is not None for v in (metrics.disk_percent, metrics.disk_used_gb, metrics.disk_total_gb)):
        return DiskFilesystem(
            filesystem="/",
            usage_percent=metrics.disk_percent,
            used_gb=metrics.disk_used_gb,
            total_gb=metrics.disk_total_gb,
        )
    return None


def normalize_metrics(metrics: MetricsPayload) -> list[MetricPoint]:
    points: list[MetricPoint | None] = [
        _point(CPU_USAGE, _cpu_usage(metrics), UNIT_PERCENT),
        _point(CPU_CORES, metrics.cores, UNIT_COUNT),
        _point(MEMORY_USAGE, _memory_usage(metrics), UNIT_PERCENT),
        _point(MEMORY_USED, _memory_used(metrics), UNIT_MB),
        _point(MEMORY_TOTAL, _memory_total(metrics), UNIT_MB),
        _point(MEMORY_AVAILABLE, metrics.available_mb, UNIT_MB),
        _point(LOAD_AVERAGE, _load_1m(metrics), UNIT_RATIO),
        _point(UPTIME, metrics.uptime_seconds, UNIT_SECONDS),
        _point(PROCESS_COUNT, metrics.process_count, UNIT_COUNT),
    ]

    if metrics.disks:
        for disk in metrics.disks:
            fs = disk.filesystem
            points.extend(
                [
                    _point(DISK_USAGE, disk.usage_percent, UNIT_PERCENT, filesystem=fs),
                    _point(DISK_USED, disk.used_gb, UNIT_GB, filesystem=fs),
                    _point(DISK_TOTAL, disk.total_gb, UNIT_GB, filesystem=fs),
                    _point(DISK_AVAILABLE, disk.available_gb, UNIT_GB, filesystem=fs),
                ]
            )
    else:
        primary = _primary_disk(metrics)
        if primary:
            fs = primary.filesystem
            points.extend(
                [
                    _point(DISK_USAGE, primary.usage_percent, UNIT_PERCENT, filesystem=fs),
                    _point(DISK_USED, primary.used_gb, UNIT_GB, filesystem=fs),
                    _point(DISK_TOTAL, primary.total_gb, UNIT_GB, filesystem=fs),
                ]
            )

    return [point for point in points if point is not None]
