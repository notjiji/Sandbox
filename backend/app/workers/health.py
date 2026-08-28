"""Celery worker and beat health probes for Compose healthchecks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.worker.health")


def check_redis_broker() -> None:
    settings = get_settings()
    if not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL is not configured")

    try:
        import redis
    except ImportError as exc:
        raise RuntimeError("redis package is required for worker health checks") from exc

    client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=3, socket_timeout=3)
    if not client.ping():
        raise RuntimeError("redis broker ping failed")


def check_worker_responsive() -> None:
    inspector = celery_app.control.inspect(timeout=3.0)
    ping = inspector.ping()
    if not ping:
        raise RuntimeError("no celery workers responded to inspect ping")
    logger.info("celery worker ping ok", extra={"workers": list(ping.keys())})


def check_beat_process(*, pidfile: str | None = None) -> None:
    path = Path(pidfile or os.environ.get("CELERY_BEAT_PIDFILE", "/tmp/celerybeat.pid"))
    if not path.is_file():
        raise RuntimeError(f"celery beat pidfile missing: {path}")

    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"invalid celery beat pidfile: {path}") from exc

    os.kill(pid, 0)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python -m app.workers.health [worker|beat]", file=sys.stderr)
        return 2

    target = args[0].lower()
    try:
        check_redis_broker()
        if target == "worker":
            check_worker_responsive()
        elif target == "beat":
            check_beat_process()
        else:
            print(f"unknown target: {target}", file=sys.stderr)
            return 2
    except Exception as exc:
        logger.error("health check failed", extra={"target": target, "error": str(exc)})
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
