"""Security finding engine — a security condition exists.

Operational events (CPU, disk, offline) are alerts, not findings.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.findings.constants import CATEGORY_SERVER_SECURITY
from app.findings.enums import FindingSeverity
from app.monitoring.schemas import AgentIngestRequest


@dataclass(frozen=True)
class FindingCandidate:
    code: str
    title: str
    message: str
    severity: FindingSeverity
    evidence: str | None = None
    category: str = CATEGORY_SERVER_SECURITY


def evaluate_findings(payload: AgentIngestRequest) -> list[FindingCandidate]:
    candidates: list[FindingCandidate] = []
    security = payload.security

    firewall = security.firewall
    if firewall and firewall.enabled is False:
        candidates.append(
            FindingCandidate(
                code="FIREWALL_INACTIVE",
                title="Firewall is not active",
                message=(
                    "Current: host firewall reported as disabled\n\n"
                    "Recommendation: Enable the host firewall and set a default-deny incoming policy."
                ),
                severity=FindingSeverity.HIGH,
                evidence=f"backend={firewall.backend or 'unknown'}",
            )
        )

    ssh = security.ssh
    if ssh:
        if ssh.permit_root_login is True:
            current = ssh.permit_root_login_raw or "yes"
            candidates.append(
                FindingCandidate(
                    code="SSH_ROOT_LOGIN",
                    title="SSH Root Login Enabled",
                    message=(
                        f"Current: PermitRootLogin {current}\n\n"
                        "Recommendation: Set PermitRootLogin no (or prohibit-password) "
                        "and administer the host via a non-root user with key-based auth."
                    ),
                    severity=FindingSeverity.HIGH,
                    evidence=f"PermitRootLogin={current}",
                )
            )
        if ssh.password_authentication is True:
            current = ssh.password_authentication_raw or "yes"
            candidates.append(
                FindingCandidate(
                    code="SSH_PASSWORD_AUTH",
                    title="SSH Password Authentication Enabled",
                    message=(
                        f"Current: PasswordAuthentication {current}\n\n"
                        "Recommendation: Disable password authentication and use "
                        "key-based authentication."
                    ),
                    severity=FindingSeverity.MEDIUM,
                    evidence=f"PasswordAuthentication={current}",
                )
            )
        if ssh.pubkey_authentication is False:
            current = ssh.pubkey_authentication_raw or "no"
            candidates.append(
                FindingCandidate(
                    code="SSH_PUBKEY_DISABLED",
                    title="SSH Public Key Authentication Disabled",
                    message=(
                        f"Current: PubkeyAuthentication {current}\n\n"
                        "Recommendation: Enable PubkeyAuthentication yes so hosts can use "
                        "key-based login instead of passwords."
                    ),
                    severity=FindingSeverity.HIGH,
                    evidence=f"PubkeyAuthentication={current}",
                )
            )
        if ssh.protocol and "1" in str(ssh.protocol).split(","):
            candidates.append(
                FindingCandidate(
                    code="SSH_PROTOCOL_LEGACY",
                    title="SSH Protocol 1 Enabled",
                    message=(
                        f"Current: Protocol {ssh.protocol}\n\n"
                        "Recommendation: Use Protocol 2 only. SSH protocol 1 is obsolete and insecure."
                    ),
                    severity=FindingSeverity.CRITICAL,
                    evidence=f"Protocol={ssh.protocol}",
                )
            )

    fail2ban = security.fail2ban
    if fail2ban:
        installed = fail2ban.installed
        running = fail2ban.running if fail2ban.running is not None else fail2ban.enabled
        if installed is False:
            candidates.append(
                FindingCandidate(
                    code="FAIL2BAN_NOT_INSTALLED",
                    title="Fail2Ban is not installed",
                    message=(
                        "Current: Fail2Ban not installed\n\n"
                        "Recommendation: Install and enable Fail2Ban to limit brute-force "
                        "authentication attempts."
                    ),
                    severity=FindingSeverity.MEDIUM,
                    evidence="fail2ban.installed=false",
                )
            )
        elif running is False:
            candidates.append(
                FindingCandidate(
                    code="FAIL2BAN_INACTIVE",
                    title="Fail2Ban is not running",
                    message=(
                        "Current: Fail2Ban installed but inactive\n\n"
                        "Recommendation: Start and enable the fail2ban service so jails can ban "
                        "abusive IPs."
                    ),
                    severity=FindingSeverity.MEDIUM,
                    evidence="fail2ban.running=false",
                )
            )

    updates = security.updates
    if updates and (updates.security or 0) > 0:
        security_count = updates.security or 0
        available_count = updates.available or 0
        candidates.append(
            FindingCandidate(
                code="SECURITY_UPDATES_PENDING",
                title=f"{security_count} security update{'s' if security_count != 1 else ''} pending",
                message=(
                    f"Current: {security_count} security update(s), "
                    f"{available_count} total available"
                    f"{f' ({updates.manager})' if updates.manager else ''}\n\n"
                    "Recommendation: Apply security updates promptly to reduce exposure "
                    "from known vulnerabilities."
                ),
                severity=FindingSeverity.MEDIUM,
                evidence=f"security={security_count}, available={available_count}",
            )
        )

    return candidates
