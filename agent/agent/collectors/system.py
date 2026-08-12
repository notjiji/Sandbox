from __future__ import annotations

import platform
import socket


def collect() -> dict:
    return {
        "os": f"{platform.system()} {platform.release()}".strip(),
        "kernel": platform.version(),
        "arch": platform.machine(),
        "hostname": socket.gethostname(),
    }
