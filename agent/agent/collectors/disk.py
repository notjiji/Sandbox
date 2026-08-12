from __future__ import annotations

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {"disk_percent": None, "disk_used_gb": None, "disk_total_gb": None}
    disk = psutil.disk_usage("/")
    return {
        "disk_percent": round(float(disk.percent), 1),
        "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
        "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
    }
