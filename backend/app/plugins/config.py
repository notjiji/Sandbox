"""Per-plugin configuration exposed to administrators."""

from dataclasses import dataclass, field


@dataclass
class PluginConfig:
    """Tunable scanner behavior — no code changes required to adjust."""

    enabled: bool = True
    timeout: float = 30.0
    retries: int = 0
    parallel: bool = False
    version: str = "0.1.0"

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "timeout": self.timeout,
            "retries": self.retries,
            "parallel": self.parallel,
            "version": self.version,
        }
