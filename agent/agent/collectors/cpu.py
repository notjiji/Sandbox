from __future__ import annotations

import os

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {
            "cpu_usage": None,
            "cpu_percent": None,
            "load_1m": None,
            "load_avg": None,
            "cores": None,
        }

    cpu = round(float(psutil.cpu_percent(interval=0.4)), 1)
    load_1m = load_5m = load_15m = None
    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            load_1m, load_5m, load_15m = os.getloadavg()
            load_avg = [round(load_1m, 2), round(load_5m, 2), round(load_15m, 2)]
            load_1m = round(load_1m, 2)
        except OSError:
            pass

    cores = psutil.cpu_count(logical=True)
    return {
        "cpu_usage": cpu,
        "cpu_percent": cpu,
        "load_1m": load_1m,
        "load_avg": load_avg,
        "cores": cores,
    }
