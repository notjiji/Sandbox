from __future__ import annotations

import os

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {"cpu_percent": None, "load_avg": None}
    cpu = psutil.cpu_percent(interval=0.4)
    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            load_avg = [round(value, 2) for value in os.getloadavg()]
        except OSError:
            load_avg = None
    return {"cpu_percent": round(float(cpu), 1), "load_avg": load_avg}
