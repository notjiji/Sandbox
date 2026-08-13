from __future__ import annotations

import re
import shutil

from agent.collectors._util import run


def _parse_jail_list(output: str) -> list[str]:
    for line in output.splitlines():
        if "Jail list:" not in line:
            continue
        listed = line.split("Jail list:", 1)[-1]
        return [item.strip() for item in listed.replace("\t", " ").split(",") if item.strip()]
    return []


def _parse_currently_banned(output: str) -> int | None:
    match = re.search(r"Currently banned:\s*(\d+)", output, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _banned_for_jail(jail: str) -> int:
    output = run(["fail2ban-client", "status", jail], timeout=4.0)
    if not output:
        return 0
    return _parse_currently_banned(output) or 0


def collect() -> dict | None:
    installed = bool(shutil.which("fail2ban-client"))
    running = False
    jails: list[str] = []
    banned_ips = 0

    if shutil.which("systemctl"):
        status = run(["systemctl", "is-active", "fail2ban"], timeout=3.0)
        running = (status or "").strip() == "active"

    if installed:
        # `fail2ban-client ping` / status confirms the daemon answers.
        status_output = run(["fail2ban-client", "status"], timeout=5.0)
        if status_output and "Jail list:" in status_output:
            running = True
            jails = _parse_jail_list(status_output)
            for jail in jails:
                banned_ips += _banned_for_jail(jail)
        elif not running:
            # Binary present but service not answering.
            running = False

    if not installed and not running:
        # No Fail2Ban tooling and not active via systemd.
        if not shutil.which("systemctl"):
            return None
        # systemctl exists but unit may still be absent — report as not installed.
        unit = run(["systemctl", "status", "fail2ban"], timeout=3.0)
        if unit is None or "could not be found" in (unit or "").lower() or "not-found" in (unit or "").lower():
            return {
                "installed": False,
                "enabled": False,
                "running": False,
                "jails": [],
                "jail_count": 0,
                "banned_ips": 0,
            }

    return {
        "installed": installed or running,
        "enabled": running,
        "running": running,
        "jails": jails,
        "jail_count": len(jails),
        "banned_ips": banned_ips if running else (0 if installed else None),
    }
