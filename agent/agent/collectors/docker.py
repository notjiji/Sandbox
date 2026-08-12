from __future__ import annotations

import shutil

from agent.collectors._util import run


def collect() -> dict | None:
    if not shutil.which("docker"):
        return {"installed": False, "running": False, "containers": None}
    info = run(["docker", "info", "--format", "{{.ServerVersion}}"])
    running = info is not None and "error" not in (info or "").lower()
    containers = None
    ps_output = run(["docker", "ps", "-q"])
    if ps_output is not None:
        containers = len([line for line in ps_output.splitlines() if line.strip()])
    return {"installed": True, "running": running, "containers": containers}
