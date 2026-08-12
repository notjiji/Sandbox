from __future__ import annotations

import time

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {"uptime_seconds": None}
    boot = getattr(psutil, "boot_time", lambda: time.time())()
    return {"uptime_seconds": int(max(0, time.time() - boot))}
