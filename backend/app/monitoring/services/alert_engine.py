"""Threshold and security-check evaluation. Facts come from the agent payload."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.monitoring.enums import AlertSeverity
from app.monitoring.schemas import AgentIngestRequest, MetricsPayload

CPU_HIGH = 90.0
RAM_HIGH = 90.0
DISK_WARN = 80.0
DISK_HIGH = 90.0
DISK_CRITICAL = 95.0


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


def evaluate_ingest(payload: AgentIngestRequest) -> list[AlertCandidate]:
    candidates: list[AlertCandidate] = []
    metrics = payload.metrics
    security = payload.security

    cpu = _cpu_percent(metrics)
    if cpu is not None and cpu >= CPU_HIGH:
        cores = f", cores={metrics.cores}" if metrics.cores else ""
        load = f", load_1m={metrics.load_1m}" if metrics.load_1m is not None else ""
        candidates.append(
            AlertCandidate(
                code="CPU_HIGH",
                title="High CPU usage",
                message=f"CPU usage is {cpu:.0f}%.",
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
                message=f"Memory usage is {ram:.0f}%.",
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

    firewall = security.firewall
    if firewall and firewall.enabled is False:
        candidates.append(
            AlertCandidate(
                code="FIREWALL_INACTIVE",
                title="Firewall is not active",
                message="Host firewall reported as disabled.",
                severity=AlertSeverity.HIGH,
                evidence=f"backend={firewall.backend or 'unknown'}",
            )
        )

    ssh = security.ssh
    if ssh:
        if ssh.permit_root_login is True:
            candidates.append(
                AlertCandidate(
                    code="SSH_ROOT_LOGIN",
                    title="SSH root login is enabled",
                    message="PermitRootLogin is enabled on this host.",
                    severity=AlertSeverity.HIGH,
                    evidence="PermitRootLogin=yes",
                )
            )
        if ssh.password_authentication is True:
            candidates.append(
                AlertCandidate(
                    code="SSH_PASSWORD_AUTH",
                    title="SSH password authentication is enabled",
                    message="PasswordAuthentication is enabled; prefer key-based auth.",
                    severity=AlertSeverity.MEDIUM,
                    evidence="PasswordAuthentication=yes",
                )
            )

    fail2ban = security.fail2ban
    if fail2ban and fail2ban.enabled is False:
        candidates.append(
            AlertCandidate(
                code="FAIL2BAN_INACTIVE",
                title="Fail2Ban is not running",
                message="Intrusion prevention (Fail2Ban) is inactive.",
                severity=AlertSeverity.MEDIUM,
                evidence="fail2ban.enabled=false",
            )
        )

    updates = security.updates
    if updates and (updates.security or 0) > 0:
        candidates.append(
            AlertCandidate(
                code="UPDATES_AVAILABLE",
                title="Security updates available",
                message=f"{updates.security} security update(s) available ({updates.available or 0} total).",
                severity=AlertSeverity.MEDIUM,
                evidence=f"security={updates.security}, available={updates.available}",
            )
        )

    return candidates
