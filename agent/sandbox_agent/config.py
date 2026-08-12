from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    api_url: str
    token: str
    interval_seconds: int
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "AgentConfig":
        api_url = os.environ.get("SANDBOX_API_URL", "").rstrip("/")
        token = os.environ.get("SANDBOX_AGENT_TOKEN", "").strip()
        if not api_url:
            raise SystemExit("SANDBOX_API_URL is required")
        if not token:
            raise SystemExit("SANDBOX_AGENT_TOKEN is required")
        interval = int(os.environ.get("SANDBOX_AGENT_INTERVAL", "60"))
        timeout = float(os.environ.get("SANDBOX_AGENT_TIMEOUT", "15"))
        return cls(
            api_url=api_url,
            token=token,
            interval_seconds=max(15, interval),
            timeout_seconds=max(5.0, timeout),
        )
