from __future__ import annotations

from typing import Any

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {"process_count": None, "processes": []}

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
    return {"process_count": len(processes), "processes": processes[:15]}
