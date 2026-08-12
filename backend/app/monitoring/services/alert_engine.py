"""Threshold and security-check evaluation. Facts come from the agent payload."""

from __future__ import annotations

from dataclasses import dataclass

from app.monitoring.enums import AlertSeverity
from app.monitoring.schemas import AgentIngestRequest


@dataclass(frozen=True)
class AlertCandidate:
    code: str
    title: str
    message: str
    severity: AlertSeverity
    evidence: str | None = None


CPU_HIGH = 90.0
RAM_HIGH = 90.0
DISK_HIGH = 90.0
DISK_CRITICAL = 95.0


def evaluate_ingest(payload: AgentIngestRequest) -> list[AlertCandidate]:
    candidates: list[AlertCandidate] = []
    metrics = payload.metrics
    security = payload.security

    if metrics.cpu_percent is not None and metrics.cpu_percent >= CPU_HIGH:
        candidates.append(
            AlertCandidate(
                code="CPU_HIGH",
                title="High CPU usage",
                message=f"CPU usage is {metrics.cpu_percent:.0f}%.",
                severity=AlertSeverity.HIGH,
                evidence=f"cpu_percent={metrics.cpu_percent}",
            )
        )

    if metrics.ram_percent is not None and metrics.ram_percent >= RAM_HIGH:
        candidates.append(
            AlertCandidate(
                code="RAM_HIGH",
                title="High memory usage",
                message=f"RAM usage is {metrics.ram_percent:.0f}%.",
                severity=AlertSeverity.HIGH,
                evidence=f"ram_percent={metrics.ram_percent}",
            )
        )

    if metrics.disk_percent is not None:
        if metrics.disk_percent >= DISK_CRITICAL:
            candidates.append(
                AlertCandidate(
                    code="DISK_CRITICAL",
                    title="Disk space critically low",
                    message=f"Disk usage is {metrics.disk_percent:.0f}%.",
                    severity=AlertSeverity.CRITICAL,
                    evidence=f"disk_percent={metrics.disk_percent}",
                )
            )
        elif metrics.disk_percent >= DISK_HIGH:
            candidates.append(
                AlertCandidate(
                    code="DISK_HIGH",
                    title="Disk space running low",
                    message=f"Disk usage is {metrics.disk_percent:.0f}%.",
                    severity=AlertSeverity.HIGH,
                    evidence=f"disk_percent={metrics.disk_percent}",
                )
            )

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
