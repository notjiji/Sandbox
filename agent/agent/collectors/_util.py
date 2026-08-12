from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run(command: list[str], *, timeout: float = 3.0) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0:
        return output or None
    return output


def read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def load_psutil():
    try:
        import psutil
    except ImportError:
        return None
    return psutil
