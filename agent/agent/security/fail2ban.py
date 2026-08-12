from __future__ import annotations

import shutil

from agent.collectors._util import run


def collect() -> dict | None:
    if not shutil.which("fail2ban-client") and not shutil.which("systemctl"):
        return None
    enabled = False
    jails: list[str] = []
    if shutil.which("systemctl"):
        status = run(["systemctl", "is-active", "fail2ban"])
        enabled = (status or "").strip() == "active"
    if shutil.which("fail2ban-client"):
        output = run(["fail2ban-client", "status"])
        if output and "Jail list:" in output:
            enabled = True
            for line in output.splitlines():
                if "Jail list:" in line:
                    listed = line.split("Jail list:", 1)[-1]
                    jails = [item.strip() for item in listed.split(",") if item.strip()]
    if not shutil.which("fail2ban-client") and not enabled:
        return {"enabled": False, "jails": []}
    return {"enabled": enabled, "jails": jails}
