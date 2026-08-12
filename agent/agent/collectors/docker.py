from __future__ import annotations

import json
import shutil

from agent.collectors._util import run


def _parse_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _container_rows(limit: int = 50) -> list[dict]:
    """Lightweight per-container facts for future dashboard columns (CPU/mem later)."""
    output = run(
        [
            "docker",
            "ps",
            "-a",
            "--no-trunc",
            "--format",
            "{{json .}}",
        ],
        timeout=5.0,
    )
    if not output:
        return []

    rows: list[dict] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = (item.get("Names") or item.get("Name") or "").split(",")[0].strip()
        status_raw = (item.get("Status") or item.get("State") or "").strip()
        state = (item.get("State") or "").strip().lower()
        if not state:
            lowered = status_raw.lower()
            if lowered.startswith("up"):
                state = "running"
            elif lowered.startswith("exited") or lowered.startswith("created"):
                state = "stopped"
            else:
                state = status_raw or "unknown"
        image = (item.get("Image") or "").strip() or None
        restart_count = None
        # RestartCount is not in `ps` format by default; leave None for V1.
        rows.append(
            {
                "name": name or (item.get("ID") or "")[:12],
                "status": state,
                "image": image,
                "cpu_percent": None,
                "memory_mb": None,
                "restart_count": restart_count,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def collect() -> dict | None:
    if not shutil.which("docker"):
        return {
            "installed": False,
            "running": False,
            "version": None,
            "containers": None,
            "containers_running": None,
            "containers_stopped": None,
            "images": None,
            "container_list": [],
        }

    # Prefer structured `docker info` when the engine is reachable.
    info_raw = run(["docker", "info", "--format", "{{json .}}"], timeout=5.0)
    if info_raw:
        try:
            info = json.loads(info_raw)
        except json.JSONDecodeError:
            info = None
        if isinstance(info, dict) and not info.get("ServerErrors"):
            version = info.get("ServerVersion") or None
            containers = _parse_int(info.get("Containers"))
            running = _parse_int(info.get("ContainersRunning"))
            stopped = _parse_int(info.get("ContainersStopped"))
            paused = _parse_int(info.get("ContainersPaused")) or 0
            if stopped is None and containers is not None and running is not None:
                stopped = max(0, containers - running - paused)
            images = _parse_int(info.get("Images"))
            return {
                "installed": True,
                "running": True,
                "version": version,
                "containers": containers,
                "containers_running": running,
                "containers_stopped": stopped,
                "images": images,
                "container_list": _container_rows(),
            }

    # Docker binary present but engine not responding.
    version = run(["docker", "version", "--format", "{{.Client.Version}}"], timeout=3.0)
    return {
        "installed": True,
        "running": False,
        "version": version,
        "containers": None,
        "containers_running": None,
        "containers_stopped": None,
        "images": None,
        "container_list": [],
    }
