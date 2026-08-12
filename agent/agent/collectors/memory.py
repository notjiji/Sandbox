from __future__ import annotations

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {"ram_percent": None, "ram_used_mb": None, "ram_total_mb": None}
    memory = psutil.virtual_memory()
    return {
        "ram_percent": round(float(memory.percent), 1),
        "ram_used_mb": round(memory.used / (1024 * 1024), 1),
        "ram_total_mb": round(memory.total / (1024 * 1024), 1),
    }
