from __future__ import annotations

import shutil

from agent.collectors._util import run

# Cap payload size; unexpected long lists are still useful later for expected-service checks.
_MAX_SERVICES = 250


def _normalize_status(active: str) -> str:
    value = (active or "").strip().lower()
    if value in {"running", "active"}:
        return "RUNNING"
    if value in {"exited", "dead", "inactive"}:
        return "STOPPED"
    if value == "failed":
        return "FAILED"
    if value == "activating":
        return "STARTING"
    if value:
        return value.upper()
    return "UNKNOWN"


def collect() -> dict:
    """Collect Linux systemd service facts only — no malice classification."""
    if not shutil.which("systemctl"):
        return {"services": []}

    output = run(
        [
            "systemctl",
            "list-units",
            "--type=service",
            "--state=running",
            "--no-pager",
            "--no-legend",
            "--plain",
        ],
        timeout=5.0,
    )
    if not output:
        return {"services": []}

    services: list[dict] = []
    seen: set[str] = set()
    for line in output.splitlines():
        parts = line.split()
        if not parts:
            continue
        unit = parts[0]
        if not unit.endswith(".service"):
            continue
        name = unit[: -len(".service")]
        if not name or name in seen:
            continue
        # Skip template/instance noise like user@1000 when name starts with weird chars? Keep all facts.
        seen.add(name)
        # Format: UNIT LOAD ACTIVE SUB DESCRIPTION...
        # Prefer SUB (running) when present; fall back to ACTIVE.
        status = "RUNNING"
        if len(parts) >= 4:
            status = _normalize_status(parts[3])
        elif len(parts) >= 3:
            status = _normalize_status(parts[2])
        services.append({"name": name, "status": status})
        if len(services) >= _MAX_SERVICES:
            break

    services.sort(key=lambda item: item["name"].lower())
    return {"services": services}
