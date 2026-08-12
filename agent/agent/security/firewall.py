from __future__ import annotations

import shutil

from agent.collectors._util import run


def collect() -> dict | None:
    if shutil.which("ufw"):
        output = run(["ufw", "status"])
        if output is None:
            return {"enabled": None, "backend": "ufw"}
        enabled = "Status: active" in output
        incoming = None
        for line in output.splitlines():
            if "Default:" in line:
                incoming = line.split("Default:", 1)[-1].strip()
                break
        return {"enabled": enabled, "backend": "ufw", "default_incoming": incoming}
    if shutil.which("firewall-cmd"):
        output = run(["firewall-cmd", "--state"])
        return {"enabled": (output or "").strip() == "running", "backend": "firewalld"}
    return None
