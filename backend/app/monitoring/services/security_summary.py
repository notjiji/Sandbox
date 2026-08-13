"""Compact security check tones for dashboard server cards."""

from __future__ import annotations

from app.monitoring.schemas import (
    OrgServerSecurityCheck,
    OrgServerSecuritySummary,
    SecurityPayload,
)

UNKNOWN = OrgServerSecurityCheck(status="unknown")


def _ok(detail: str | None = None) -> OrgServerSecurityCheck:
    return OrgServerSecurityCheck(status="ok", detail=detail)


def _warn(detail: str | None = None) -> OrgServerSecurityCheck:
    return OrgServerSecurityCheck(status="warn", detail=detail)


def summarize_security(security: SecurityPayload | None) -> OrgServerSecuritySummary:
    if security is None:
        return OrgServerSecuritySummary(
            ssh=UNKNOWN,
            firewall=UNKNOWN,
            fail2ban=UNKNOWN,
            updates=UNKNOWN,
            docker=UNKNOWN,
        )

    ssh = security.ssh
    if ssh is None:
        ssh_check = UNKNOWN
    elif (
        ssh.permit_root_login is True
        or ssh.password_authentication is True
        or ssh.pubkey_authentication is False
        or (ssh.protocol is not None and "1" in str(ssh.protocol).split(","))
    ):
        ssh_check = _warn()
    else:
        ssh_check = _ok()

    firewall = security.firewall
    if firewall is None or firewall.enabled is None:
        firewall_check = UNKNOWN
    elif firewall.enabled is False:
        firewall_check = _warn()
    else:
        firewall_check = _ok()

    fail2ban = security.fail2ban
    if fail2ban is None:
        fail2ban_check = UNKNOWN
    else:
        running = fail2ban.running if fail2ban.running is not None else fail2ban.enabled
        if fail2ban.installed is False or running is False:
            fail2ban_check = _warn()
        elif fail2ban.installed is True and running is True:
            fail2ban_check = _ok()
        else:
            fail2ban_check = UNKNOWN

    updates = security.updates
    if updates is None or updates.security is None:
        updates_check = UNKNOWN
    elif updates.security > 0:
        updates_check = _warn(str(updates.security))
    else:
        updates_check = _ok()

    docker = security.docker
    if docker is None:
        docker_check = UNKNOWN
    elif docker.installed is False:
        docker_check = _ok()
    elif docker.running is False:
        docker_check = _warn()
    elif docker.running is True:
        docker_check = _ok()
    else:
        docker_check = UNKNOWN

    return OrgServerSecuritySummary(
        ssh=ssh_check,
        firewall=firewall_check,
        fail2ban=fail2ban_check,
        updates=updates_check,
        docker=docker_check,
    )


def summarize_security_payload(raw: dict | None) -> OrgServerSecuritySummary:
    if not raw:
        return summarize_security(None)
    try:
        return summarize_security(SecurityPayload.model_validate(raw))
    except Exception:
        return summarize_security(None)
