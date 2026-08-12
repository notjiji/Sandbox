from __future__ import annotations

import logging
import signal
import sys
import time

from sandbox_agent import __version__
from sandbox_agent.client import AgentClient
from sandbox_agent.collector import collect_payload
from sandbox_agent.config import AgentConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s sandbox-agent %(message)s",
)
logger = logging.getLogger("sandbox_agent")

_running = True


def _handle_stop(_signum: int, _frame: object) -> None:
    global _running
    _running = False


def main() -> int:
    config = AgentConfig.from_env()
    client = AgentClient(
        api_url=config.api_url,
        token=config.token,
        timeout_seconds=config.timeout_seconds,
    )
    interval = config.interval_seconds
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    logger.info("starting agent v%s → %s", __version__, config.api_url)
    while _running:
        try:
            payload = collect_payload(agent_version=__version__)
            result = client.ingest(payload)
            interval = int(result.get("next_interval_seconds") or interval)
            logger.info(
                "heartbeat ok status=%s alerts_open=%s",
                result.get("agent_status"),
                result.get("alerts_open"),
            )
        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            logger.warning("heartbeat failed: %s", exc)
            interval = min(interval * 2, 300)
        for _ in range(max(1, interval)):
            if not _running:
                break
            time.sleep(1)
    logger.info("agent stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
