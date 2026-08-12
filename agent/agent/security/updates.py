from __future__ import annotations

from pathlib import Path

from agent.collectors._util import run


def collect() -> dict | None:
    checker = "/usr/lib/update-notifier/apt-check"
    if not Path(checker).exists():
        return None
    output = run([checker], timeout=8.0)
    if output and ";" in output:
        parts = output.strip().split(";")
        try:
            available = int(parts[0])
            security = int(parts[1]) if len(parts) > 1 else 0
            return {"available": available, "security": security}
        except ValueError:
            return None
    return None
