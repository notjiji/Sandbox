from __future__ import annotations

import time
from datetime import UTC, datetime

from agent.collectors._util import load_psutil


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {
            "uptime_seconds": None,
            "boot_time": None,
            "last_reboot_at": None,
        }

    boot_ts = getattr(psutil, "boot_time", lambda: time.time())()
    uptime_seconds = int(max(0, time.time() - boot_ts))
    boot_time = datetime.fromtimestamp(boot_ts, tz=UTC).isoformat()
    return {
        "uptime_seconds": uptime_seconds,
        "boot_time": boot_time,
        "last_reboot_at": boot_time,
    }
