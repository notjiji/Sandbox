from __future__ import annotations

import re
import shutil
from pathlib import Path

from agent.collectors._util import run


def _reboot_required() -> bool:
    return Path("/var/run/reboot-required").exists()


def _from_apt_check() -> dict | None:
    checker = "/usr/lib/update-notifier/apt-check"
    if not Path(checker).exists():
        return None
    output = run([checker], timeout=8.0)
    if not output or ";" not in output:
        return None
    # apt-check writes "N;M" to stderr; run() captures it.
    parts = output.strip().split(";")
    try:
        available = int(parts[0])
        security = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return None
    return {
        "available": available,
        "security": security,
        "manager": "apt",
        "reboot_required": _reboot_required(),
    }


def _from_apt_list() -> dict | None:
    if not shutil.which("apt"):
        return None
    output = run(["apt", "list", "--upgradable"], timeout=12.0)
    if output is None:
        return None
    packages: list[str] = []
    security = 0
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Listing"):
            continue
        packages.append(line.split("/", 1)[0])
        lower = line.lower()
        if "security" in lower or "-security" in lower:
            security += 1
    return {
        "available": len(packages),
        "security": security,
        "manager": "apt",
        "reboot_required": _reboot_required(),
    }


def _from_dnf() -> dict | None:
    binary = "dnf" if shutil.which("dnf") else ("yum" if shutil.which("yum") else None)
    if not binary:
        return None

    # Exit code 100 = updates available; run() still returns stdout on non-zero.
    check = run([binary, "check-update", "-q"], timeout=20.0)
    available = 0
    if check:
        for line in check.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Obsoleting") or stripped.startswith("Security:"):
                continue
            if re.match(r"^[^\s]+\s+[^\s]+\s+[^\s]+", stripped):
                available += 1

    security = 0
    info = run([binary, "updateinfo", "list", "security", "-q"], timeout=15.0)
    if info:
        for line in info.splitlines():
            if line.strip() and not line.lower().startswith("last metadata"):
                security += 1

    return {
        "available": available,
        "security": security,
        "manager": binary,
        "reboot_required": _reboot_required(),
    }


def collect() -> dict | None:
    """Read-only package update counts for risk findings. Never installs updates."""
    for collector in (_from_apt_check, _from_apt_list, _from_dnf):
        result = collector()
        if result is not None:
            return result

    if _reboot_required():
        return {
            "available": None,
            "security": None,
            "manager": None,
            "reboot_required": True,
        }
    return None
