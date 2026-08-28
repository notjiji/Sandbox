# Background Jobs (Celery)

Long-running work runs outside the HTTP request cycle via Celery workers backed by Redis.

## Architecture

```
FastAPI API
    → create record (scan/report) with pending/generating status
    → task.delay(...)
    → Redis broker
    → Celery worker
    → service/executor completes work
    → status updated in DB
```

Frontend polls or uses TanStack Query refetch while status is in-progress.

## Worker configuration

File: `backend/app/workers/celery_app.py`

| Setting | Value |
|---------|-------|
| Broker | `REDIS_URL` |
| Result backend | `REDIS_URL` |
| Serializer | JSON |
| Timezone | UTC |

### Included task modules

- `app.jobs.example` — heartbeat
- `app.jobs.scans` — scan execution + schedule checker
- `app.jobs.reports` — PDF report generation
- `app.jobs.monitoring` — stale agent liveness / `SERVER_OFFLINE`

## Tasks

### Scans

| Task | Name | Trigger |
|------|------|---------|
| `execute_scan` | `app.jobs.scans.execute_scan` | API queues after scan run |
| `check_due_schedules` | `app.jobs.scans.check_due_schedules` | Celery Beat every minute |

Scan inline mode: `SCAN_RUN_INLINE=true` in development runs synchronously without queueing.

### Reports

| Task | Name | Trigger |
|------|------|---------|
| `generate_report_task` | `app.jobs.reports.generate_report` | API after report create with `generate: true` |

Report inline mode: `REPORT_RUN_INLINE=true` in development.

### Heartbeat

| Task | Schedule |
|------|----------|
| `app.jobs.example.heartbeat` | Every 5 minutes |

Confirms worker connectivity.

### Monitoring

| Task | Schedule |
|------|----------|
| `app.jobs.monitoring.reconcile_offline_agents` | Every minute |

Marks agents offline after 5 minutes without a heartbeat and opens `SERVER_OFFLINE`. Delayed (1–5 minutes) is computed on read and does not persist.

## Celery Beat

Scheduled tasks defined in `celery_app.conf.beat_schedule`:

- **`check-scan-schedules`** — evaluates cron schedules, creates/queues due scans
- **`reconcile-offline-agents`** — expires stale monitoring agents
- **`reconcile-stale-jobs`** — fails scans/reports stuck after worker crash or timeout

**Run exactly one beat instance** per environment. See [../deployment/workers.md](../deployment/workers.md).

Beat runs as a separate Docker service (`celery-beat` in docker-compose) with `--pidfile` for healthchecks.

## Running locally

```bash
make up                    # Starts redis, worker, beat
docker compose logs -f celery-worker celery-beat
```

## Error handling

Tasks use `bind=True` with logging on failure. Failed scans set scan status to `failed`; failed reports set report status to `failed`. DB transactions are committed or rolled back in `finally` blocks.

### Reliability (production)

| Mechanism | Location |
|-----------|----------|
| Soft/hard time limits | `celery_app.conf.task_annotations` + config timeouts |
| `task_failure` structured logging | `app/workers/job_failures.py` |
| State recovery on failure | `recover_failed_job_state` → `scan_recovery.py` |
| Stale `running`/`generating` reconcile | Beat task `reconcile_stale_jobs` (every 5 min) |
| Worker/beat healthchecks | `python -m app.workers.health` |

Full ops guide: [../deployment/workers.md](../deployment/workers.md).

## Correlation IDs

Scan tasks accept optional `correlation_id` for log tracing across API → worker → plugins.

## Related docs

- [../scan-engine.md](../scan-engine.md) — what happens inside `execute_scan`
- [../reports/generation-flow.md](../reports/generation-flow.md) — report pipeline in worker
- [../deployment/workers.md](../deployment/workers.md) — health, restart policy, timeouts

## Docker services

| Service | Command |
|---------|---------|
| `celery-worker` | `celery -A app.workers.celery_app worker` (+ healthcheck) |
| `celery-beat` | `celery -A app.workers.celery_app beat --pidfile=…` (**single replica**) |

See `docker-compose.yml` and `Makefile` targets `backend-logs`, `logs`.
