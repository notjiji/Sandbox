# Health and operations

## HTTP probes (`app/core/health.py`)

| Path | Meaning | Failure |
|------|---------|---------|
| `GET /health` | Process up, version | Always 200 if the app answers |
| `GET /health/live` | Liveness | 200 `alive` |
| `GET /health/ready` | Postgres + Redis | 503 if either disconnected |

Compose backend healthcheck hits `/health/ready`.

Rate limiter is **exempt** on these routes.

## Migrations in ops

Always `alembic upgrade head` before relying on audit hash columns or `delayed` agent status (043–045).

## Jobs

Celery must run for scheduled scans, offline agent reconcile, and non-inline scan/report execution. Inline mode can hide a missing worker in development.

Worker healthchecks: `python -m app.workers.health worker|beat` in Compose. See [workers.md](./workers.md).

## Logs

`make logs` / `make backend-logs`. Loki/Grafana if the monitoring profile is up.

Day-2 ops (restart, migrate, backup, incidents): [production-runbook.md](./production-runbook.md).

## What ops docs do not include

- Multi-node Postgres
- TLS termination beyond whatever you put in front of nginx
- Secret rotation runbooks

Backup/restore procedures: [backups.md](./backups.md) and the runbook.
