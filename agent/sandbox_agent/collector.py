from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]


def _run(command: list[str], *, timeout: float = 3.0) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return (completed.stdout or completed.stderr or "").strip() or None
    return (completed.stdout or "").strip()


def _read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _parse_sshd_config(raw: str) -> dict[str, Any]:
    permit_root = None
    password_auth = None
    port = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0].lower(), parts[1].strip().lower()
        if key == "permitrootlogin":
            permit_root = value not in {"no", "prohibit-password", "without-password", "forced-commands-only"}
        elif key == "passwordauthentication":
            password_auth = value == "yes"
        elif key == "port":
            try:
                port = int(value)
            except ValueError:
                port = None
    return {
        "permit_root_login": permit_root,
        "password_authentication": password_auth,
        "port": port,
    }


def _collect_metrics() -> dict[str, Any]:
    if psutil is None:
        return {}

    cpu = psutil.cpu_percent(interval=0.4)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot = getattr(psutil, "boot_time", lambda: time.time())()
    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            load_avg = [round(value, 2) for value in os.getloadavg()]
        except OSError:
            load_avg = None

    processes: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "username"]):
        try:
            info = proc.info
            rss = info.get("memory_info")
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name") or "",
                    "cpu": info.get("cpu_percent"),
                    "rss_mb": round((rss.rss / (1024 * 1024)), 1) if rss else None,
                    "user": info.get("username"),
                }
            )
        except (psutil.Error, TypeError, AttributeError):
            continue
    processes.sort(key=lambda item: item.get("rss_mb") or 0, reverse=True)

    return {
        "cpu_percent": round(float(cpu), 1),
        "ram_percent": round(float(memory.percent), 1),
        "ram_used_mb": round(memory.used / (1024 * 1024), 1),
        "ram_total_mb": round(memory.total / (1024 * 1024), 1),
        "disk_percent": round(float(disk.percent), 1),
        "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
        "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
        "uptime_seconds": int(max(0, time.time() - boot)),
        "load_avg": load_avg,
        "process_count": len(processes),
        "processes": processes[:15],
    }


def _collect_firewall() -> dict[str, Any] | None:
    if shutil.which("ufw"):
        output = _run(["ufw", "status"])
        if output is None:
            return {"enabled": None, "backend": "ufw"}
        enabled = "Status: active" in output
        incoming = None
        for line in output.splitlines():
            if "Default:" in line:
                incoming = line.split("Default:", 1)[-1].strip()
                break
        return {"enabled": enabled, "backend": "ufw", "default_incoming": incoming}
    if shutil.which("firewall-cmd"):
        output = _run(["firewall-cmd", "--state"])
        return {
            "enabled": (output or "").strip() == "running",
            "backend": "firewalld",
        }
    return None


def _collect_ssh() -> dict[str, Any] | None:
    raw = _read_text("/etc/ssh/sshd_config")
    if raw is None:
        return None
    return _parse_sshd_config(raw)


def _collect_fail2ban() -> dict[str, Any] | None:
    if not shutil.which("fail2ban-client") and not shutil.which("systemctl"):
        return None
    enabled = False
    jails: list[str] = []
    if shutil.which("systemctl"):
        status = _run(["systemctl", "is-active", "fail2ban"])
        enabled = (status or "").strip() == "active"
    if shutil.which("fail2ban-client"):
        output = _run(["fail2ban-client", "status"])
        if output and "Jail list:" in output:
            enabled = True
            for line in output.splitlines():
                if "Jail list:" in line:
                    listed = line.split("Jail list:", 1)[-1]
                    jails = [item.strip() for item in listed.split(",") if item.strip()]
    if not shutil.which("fail2ban-client") and not enabled:
        return {"enabled": False, "jails": []}
    return {"enabled": enabled, "jails": jails}


def _collect_docker() -> dict[str, Any] | None:
    if not shutil.which("docker"):
        return {"installed": False, "running": False, "containers": None}
    info = _run(["docker", "info", "--format", "{{.ServerVersion}}"])
    running = info is not None and "error" not in (info or "").lower()
    containers = None
    ps_output = _run(["docker", "ps", "-q"])
    if ps_output is not None:
        containers = len([line for line in ps_output.splitlines() if line.strip()])
    return {"installed": True, "running": running, "containers": containers}


def _collect_updates() -> dict[str, Any] | None:
    checker = "/usr/lib/update-notifier/apt-check"
    if Path(checker).exists():
        output = _run([checker], timeout=8.0)
        # apt-check writes "N;M" to stderr; _run returns stdout or stderr on failure.
        if output and ";" in output:
            parts = output.strip().split(";")
            try:
                available = int(parts[0])
                security = int(parts[1]) if len(parts) > 1 else 0
                return {"available": available, "security": security}
            except ValueError:
                pass
    return None


def _collect_system() -> dict[str, Any]:
    return {
        "os": f"{platform.system()} {platform.release()}".strip(),
        "kernel": platform.version(),
        "arch": platform.machine(),
        "hostname": socket.gethostname(),
    }


def collect_payload(*, agent_version: str) -> dict[str, Any]:
    return {
        "collected_at": datetime.now(UTC).isoformat(),
        "agent_version": agent_version,
        "hostname": socket.gethostname(),
        "metrics": _collect_metrics(),
        "security": {
            "firewall": _collect_firewall(),
            "ssh": _collect_ssh(),
            "fail2ban": _collect_fail2ban(),
            "docker": _collect_docker(),
            "updates": _collect_updates(),
            "system": _collect_system(),
        },
    }
