from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _state_dir() -> Path:
    raw = os.environ.get("SANDBOX_AGENT_HOME", "").strip()
    if raw:
        return Path(raw)
    return Path.home() / ".sandbox-agent"


@dataclass
class AgentConfig:
    api_url: str
    enrollment_token: str | None
    credential: str | None
    interval_seconds: int
    timeout_seconds: float
    state_dir: Path

    @property
    def credential_path(self) -> Path:
        return self.state_dir / "credential"

    def persist_credential(self, credential: str) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.credential_path.write_text(credential, encoding="utf-8")
        try:
            os.chmod(self.credential_path, 0o600)
        except OSError:
            pass

    def load_stored_credential(self) -> str | None:
        if not self.credential_path.exists():
            return None
        value = self.credential_path.read_text(encoding="utf-8").strip()
        return value or None

    @classmethod
    def from_env(cls) -> "AgentConfig":
        api_url = os.environ.get("SANDBOX_API_URL", "").rstrip("/")
        if not api_url:
            raise SystemExit("SANDBOX_API_URL is required")
        enrollment = os.environ.get("SANDBOX_ENROLLMENT_TOKEN", "").strip() or None
        credential = os.environ.get("SANDBOX_AGENT_CREDENTIAL", "").strip() or None
        interval = int(os.environ.get("SANDBOX_AGENT_INTERVAL", "60"))
        timeout = float(os.environ.get("SANDBOX_AGENT_TIMEOUT", "15"))
        config = cls(
            api_url=api_url,
            enrollment_token=enrollment,
            credential=credential,
            interval_seconds=max(15, interval),
            timeout_seconds=max(5.0, timeout),
            state_dir=_state_dir(),
        )
        if config.credential is None:
            config.credential = config.load_stored_credential()
        if config.credential is None and config.enrollment_token is None:
            raise SystemExit("SANDBOX_ENROLLMENT_TOKEN is required for first registration")
        return config
