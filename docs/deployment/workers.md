# Celery workers and scheduler

Background scans, PDF reports, recurring scan schedules, and monitoring reconcile run in Celery workers backed by Redis. This document covers **health checks**, **restart policy**, **failure handling**, and the **single beat scheduler** requirement so restarting one service does not leave scans or reports stuck in an unknown state.

For task names and inline vs queued mode see [jobs/README.md](../jobs/README.md). For env vars see [configuration.md](./configuration.md).

---

## Services (Compose)

| Service | Role | Scale |
|---------|------|-------|
| `celery-worker` | Executes queued scans, reports, and periodic reconcile tasks | **Horizontal** — add replicas or raise `CELERY_CONCURRENCY` |
| `celery-beat` | Publishes scheduled tasks to the broker | **Exactly one instance** — never scale horizontally |

Both services use `restart: unless-stopped`. The worker has `stop_grace_period: 120s` so in-flight tasks can finish or be re-queued cleanly (`task_acks_late`, `task_reject_on_worker_lost`).

---

## Scheduler singleton (critical)

**Run exactly one `celery-beat` container per environment.**

Multiple beat processes will duplicate scheduled work (double scan schedules, double stale-job reconcile, duplicate offline-agent checks). Compose does not enforce a replica count — operators must not run a second beat on another host without external leader election (not provided in-repo).

Beat writes its PID to `CELERY_BEAT_PIDFILE` (default `/tmp/celerybeat.pid`) and its schedule database to `/tmp/celerybeat-schedule` inside the container.

---

## Health checks

Docker healthchecks call `python -m app.workers.health`:

| Target | Command | Checks |
|--------|---------|--------|
| Worker | `python -m app.workers.health worker` | Redis broker ping + Celery `inspect ping` |
| Beat | `python -m app.workers.health beat` | Redis broker ping + beat PID file alive |

Manual check from a running container:

```bash
docker compose exec celery-worker python -m app.workers.health worker
docker compose exec celery-beat python -m app.workers.health beat
```

Exit code `0` = healthy, `1` = unhealthy.

---

## Restart policy

| Event | Expected behaviour |
|-------|-------------------|
| Worker restart / crash | Tasks with `acks_late` are re-delivered. Scans/reports left `running`/`generating` are failed by the task failure handler or the stale reconcile job. |
| Beat restart | Schedules resume from the beat schedule file; no duplicate beat should be started elsewhere. |
| Redis restart | Broker is ephemeral. Queued tasks may be lost; domain rows stay `pending`/`queued` until re-enqueued or reconciled. Postgres is the source of truth for scan/report status. |
| API restart | Does not affect in-flight worker tasks. |

Safe restart order when debugging:

```bash
docker compose restart celery-worker
# or beat only (does not stop workers):
docker compose restart celery-beat
```

Avoid `docker compose up --scale celery-beat=2` — unsupported.

---

## Task time limits

Configured in `backend/app/core/config.py` and applied via Celery `task_annotations`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SCAN_TASK_SOFT_TIMEOUT_SECONDS` | 3300 (55 min) | Soft limit — raises `SoftTimeLimitExceeded`, scan marked `failed` |
| `SCAN_TASK_HARD_TIMEOUT_SECONDS` | 3600 (60 min) | Hard kill |
| `SCAN_STALE_RUNNING_SECONDS` | 3900 (65 min) | Reconcile job fails scans still `running` after this |
| `REPORT_TASK_SOFT_TIMEOUT_SECONDS` | 600 (10 min) | Report soft timeout |
| `REPORT_TASK_HARD_TIMEOUT_SECONDS` | 900 (15 min) | Report hard kill |
| `REPORT_STALE_GENERATING_SECONDS` | 1200 (20 min) | Reconcile job fails reports still `generating` |

Stale thresholds should be **greater than** hard timeouts so the task failure path runs first; reconcile is a safety net after worker loss.

---

## Job failure handling

1. **Task body** — `execute_scan` / `generate_report_task` catch `SoftTimeLimitExceeded`, roll back, mark domain row `failed`, re-raise.
2. **`task_failure` signal** — `log_failed_job` writes structured logs (`job_type`, `task_id`, `exception_type`, `timed_out`, stack trace). `recover_failed_job_state` ensures `running`/`generating` rows are marked `failed` if still in-flight.
3. **Periodic reconcile** — Beat task `app.jobs.scans.reconcile_stale_jobs` every 5 minutes fails scans/reports exceeding stale thresholds (worker crash, hard timeout, OOM kill).

Failed job log fields (filter in Loki/Grafana or `docker compose logs`):

- `background job failed` — any Celery task exception
- `scan marked failed after worker error` / `report marked failed after worker error` — recovery
- `reconciled stale running scan` / `reconciled stale generating report` — safety net

---

## Celery reliability settings

From `backend/app/workers/celery_app.py`:

| Setting | Value | Why |
|---------|-------|-----|
| `task_acks_late` | `true` | Ack after success — task re-queued if worker dies mid-run |
| `task_reject_on_worker_lost` | `true` | Re-queue on worker loss |
| `worker_prefetch_multiplier` | `1` | Fair distribution; long scans do not hoard prefetch |

---

## Production checklist

- [ ] `SCAN_RUN_INLINE=false` and `REPORT_RUN_INLINE=false`
- [ ] Exactly **one** `celery-beat` container
- [ ] `celery-worker` healthy (`docker compose ps`)
- [ ] `celery-beat` healthy
- [ ] Redis healthy (backend `/health/ready`)
- [ ] Stale reconcile appearing in logs only after incidents (not every 5 minutes)

Related: [production-runbook.md](./production-runbook.md), [health.md](./health.md), [troubleshooting.md](./troubleshooting.md).
