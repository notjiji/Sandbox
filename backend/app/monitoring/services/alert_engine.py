"""Operational alert engine — something is happening now.

Security conditions are evaluated separately as findings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.monitoring.enums import AGENT_OFFLINE_SECONDS, AgentStatus, AlertSeverity
from app.monitoring.models import MonitoringAgent
from app.monitoring.repositories.agent_repository import effective_status
from app.monitoring.schemas import AgentIngestRequest, MetricsPayload

CPU_HIGH = 90.0
RAM_HIGH = 90.0
DISK_WARN = 80.0
DISK_HIGH = 90.0
DISK_CRITICAL = 95.0

SERVER_OFFLINE = "SERVER_OFFLINE"


@dataclass(frozen=True)
class AlertCandidate:
    code: str
    title: str
    message: str
    severity: AlertSeverity
    evidence: str | None = None


def _cpu_percent(metrics: MetricsPayload) -> float | None:
    return metrics.cpu_usage if metrics.cpu_usage is not None else metrics.cpu_percent


def _ram_percent(metrics: MetricsPayload) -> float | None:
    return metrics.usage_percent if metrics.usage_percent is not None else metrics.ram_percent


def _disk_slug(filesystem: str) -> str:
    slug = filesystem.strip("/\\").replace("/", "_").replace("\\", "_") or "root"
    return re.sub(r"[^a-zA-Z0-9_]", "_", slug)


def _disk_alert(level: str, filesystem: str) -> str:
    return f"DISK_{level}__{_disk_slug(filesystem)}"


def _disk_candidates(filesystem: str, usage_percent: float) -> list[AlertCandidate]:
    if usage_percent >= DISK_CRITICAL:
        return [
            AlertCandidate(
                code=_disk_alert("CRITICAL", filesystem),
                title=f"Disk critically low on {filesystem}",
                message=f"{filesystem} is {usage_percent:.0f}% full.",
                severity=AlertSeverity.CRITICAL,
                evidence=f"filesystem={filesystem}, usage_percent={usage_percent}",
            )
        ]
    if usage_percent >= DISK_HIGH:
        return [
            AlertCandidate(
                code=_disk_alert("HIGH", filesystem),
                title=f"Disk space low on {filesystem}",
                message=f"{filesystem} is {usage_percent:.0f}% full.",
                severity=AlertSeverity.HIGH,
                evidence=f"filesystem={filesystem}, usage_percent={usage_percent}",
            )
        ]
    if usage_percent >= DISK_WARN:
        return [
            AlertCandidate(
                code=_disk_alert("WARN", filesystem),
                title=f"Disk usage warning on {filesystem}",
                message=f"{filesystem} is {usage_percent:.0f}% full.",
                severity=AlertSeverity.MEDIUM,
                evidence=f"filesystem={filesystem}, usage_percent={usage_percent}",
            )
        ]
    return []


def evaluate_alerts(payload: AgentIngestRequest) -> list[AlertCandidate]:
    """Operational conditions: CPU, memory, disk, reboot. Not security findings."""
    candidates: list[AlertCandidate] = []
    metrics = payload.metrics

    cpu = _cpu_percent(metrics)
    if cpu is not None and cpu >= CPU_HIGH:
        cores = f", cores={metrics.cores}" if metrics.cores else ""
        load = f", load_1m={metrics.load_1m}" if metrics.load_1m is not None else ""
        candidates.append(
            AlertCandidate(
                code="CPU_HIGH",
                title="High CPU usage",
                message=f"Server CPU exceeded {cpu:.0f}%.",
                severity=AlertSeverity.HIGH,
                evidence=f"cpu_usage={cpu}{load}{cores}",
            )
        )

    ram = _ram_percent(metrics)
    if ram is not None and ram >= RAM_HIGH:
        candidates.append(
            AlertCandidate(
                code="RAM_HIGH",
                title="High memory usage",
                message=f"Server memory exceeded {ram:.0f}%.",
                severity=AlertSeverity.HIGH,
                evidence=f"usage_percent={ram}",
            )
        )

    if metrics.disks:
        for disk in metrics.disks:
            if disk.usage_percent is not None:
                candidates.extend(_disk_candidates(disk.filesystem, disk.usage_percent))
    elif metrics.disk_percent is not None:
        candidates.extend(_disk_candidates("/", metrics.disk_percent))

    updates = payload.security.updates
    if updates and updates.reboot_required is True:
        candidates.append(
            AlertCandidate(
                code="REBOOT_REQUIRED",
                title="System reboot required",
                message="Kernel or library updates require a reboot to take effect.",
                severity=AlertSeverity.LOW,
                evidence="reboot_required=true",
            )
        )

    return candidates


def server_offline_alert(agent: MonitoringAgent) -> AlertCandidate:
    hostname = agent.hostname or "server"
    return AlertCandidate(
        code=SERVER_OFFLINE,
        title="Server offline",
        message=f"{hostname} has not sent a heartbeat in {AGENT_OFFLINE_SECONDS // 60} minutes.",
        severity=AlertSeverity.HIGH,
        evidence=f"last_seen_at={agent.last_seen_at.isoformat() if agent.last_seen_at else 'never'}",
    )


def should_alert_offline(agent: MonitoringAgent, *, now: datetime | None = None) -> bool:
    if agent.status in {AgentStatus.REVOKED, AgentStatus.PENDING}:
        return False
    return effective_status(agent, now=now) == AgentStatus.OFFLINE


# Backward-compatible name used by older tests; operational alerts only.
evaluate_ingest = evaluate_alerts
