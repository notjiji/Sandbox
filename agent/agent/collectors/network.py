"""Read-only host network throughput. Never opens listeners or changes interfaces."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from agent.collectors._util import load_psutil


def _state_path() -> Path:
    raw = os.environ.get("SANDBOX_AGENT_HOME", "").strip()
    root = Path(raw) if raw else Path.home() / ".sandbox-agent"
    return root / "net_io.json"


def _load_previous() -> dict | None:
    path = _state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return {"t": float(data["t"]), "recv": float(data["recv"]), "sent": float(data["sent"])}
    except (KeyError, TypeError, ValueError):
        return None


def _save_previous(*, t: float, recv: int, sent: int) -> None:
    path = _state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"t": t, "recv": recv, "sent": sent}), encoding="utf-8")
        os.chmod(path, 0o600)
    except OSError:
        pass


def rates(previous: dict | None, now: float, recv: int, sent: int) -> tuple[float | None, float | None]:
    if previous is None:
        return None, None
    dt = now - previous["t"]
    if dt < 1:
        return None, None
    rx = max(0.0, (recv - previous["recv"]) / dt)
    tx = max(0.0, (sent - previous["sent"]) / dt)
    return rx, tx


def collect() -> dict:
    psutil = load_psutil()
    empty = {"network_rx_bytes_sec": None, "network_tx_bytes_sec": None}
    if psutil is None:
        return empty
    try:
        io = psutil.net_io_counters()
    except Exception:  # noqa: BLE001 — counters unavailable on some hosts
        return empty

    now = time.time()
    rx, tx = rates(_load_previous(), now, int(io.bytes_recv), int(io.bytes_sent))
    _save_previous(t=now, recv=int(io.bytes_recv), sent=int(io.bytes_sent))
    return {
        "network_rx_bytes_sec": round(rx, 1) if rx is not None else None,
        "network_tx_bytes_sec": round(tx, 1) if tx is not None else None,
    }
