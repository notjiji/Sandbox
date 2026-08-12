from __future__ import annotations

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {
            "total_mb": None,
            "used_mb": None,
            "available_mb": None,
            "usage_percent": None,
            "ram_percent": None,
            "ram_used_mb": None,
            "ram_total_mb": None,
        }

    memory = psutil.virtual_memory()
    total_mb = round(memory.total / (1024 * 1024), 1)
    used_mb = round(memory.used / (1024 * 1024), 1)
    available_mb = round(memory.available / (1024 * 1024), 1)
    usage_percent = round(float(memory.percent), 1)
    return {
        "total_mb": total_mb,
        "used_mb": used_mb,
        "available_mb": available_mb,
        "usage_percent": usage_percent,
        "ram_percent": usage_percent,
        "ram_used_mb": used_mb,
        "ram_total_mb": total_mb,
    }
