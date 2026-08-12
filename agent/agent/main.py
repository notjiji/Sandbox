from __future__ import annotations

import logging
import signal
import socket
import sys
import time
from datetime import UTC, datetime

from agent import __version__
from agent.client import AgentApi
from agent.collectors import collect_metrics
from agent.config import AgentConfig
from agent.security import collect_security

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s sandbox-agent %(message)s",
)
logger = logging.getLogger("sandbox_agent")

_running = True


def _handle_stop(_signum: int, _frame: object) -> None:
    global _running
    _running = False


def _ensure_credential(config: AgentConfig, client: AgentApi) -> str:
    if config.credential:
        return config.credential
    if not config.enrollment_token:
        raise SystemExit("Missing enrollment token and stored credential")
    logger.info("exchanging enrollment token for a per-server credential")
    result = client.register(
        enrollment_token=config.enrollment_token,
        hostname=socket.gethostname(),
        agent_version=__version__,
    )
    credential = str(result.get("credential") or "")
    if not credential:
        raise RuntimeError("Registration did not return a credential")
    config.persist_credential(credential)
    config.credential = credential
    logger.info("credential stored at %s", config.credential_path)
    return credential


def _payload() -> dict:
    return {
        "collected_at": datetime.now(UTC).isoformat(),
        "agent_version": __version__,
        "hostname": socket.gethostname(),
        "metrics": collect_metrics(),
        "security": collect_security(),
    }


def main() -> int:
    config = AgentConfig.from_env()
    client = AgentApi(api_url=config.api_url, timeout_seconds=config.timeout_seconds)
    interval = config.interval_seconds
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    logger.info("starting agent v%s → %s", __version__, config.api_url)
    try:
        credential = _ensure_credential(config, client)
    except Exception as exc:  # noqa: BLE001
        logger.error("registration failed: %s", exc)
        return 1

    while _running:
        try:
            result = client.ingest(credential=credential, payload=_payload())
            interval = int(result.get("next_interval_seconds") or interval)
            logger.info(
                "heartbeat ok status=%s alerts_open=%s",
                result.get("agent_status"),
                result.get("alerts_open"),
            )
        except Exception as exc:  # noqa: BLE001
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
