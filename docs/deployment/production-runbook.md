# Production runbook

Short operational guide for day-2 ops on the Compose stack. For first-time install see [installation.md](./installation.md). For hardening see [production.md](./production.md). For backup policy see [backups.md](./backups.md).

Assume you are in the repository root with a valid `.env`.

---

## Startup

```bash
docker compose up -d
```

Or: `make up`.

Then apply schema if this is a new database or you have pending migrations:

```bash
make migrate
```

Confirm containers:

```bash
docker compose ps
```

Expected: `postgres` and `redis` healthy; `backend` healthy (readiness); `celery-worker`, `celery-beat`, `nginx`, `frontend` running.

---

## Health

Health routes are on the **backend** (port 8000 inside the network). Nginx does **not** expose them on `:80` by default — check from the container or your TLS proxy if you added a route.

| Path | Meaning | OK | Fail |
|------|---------|----|------|
| `GET /health` | Process up + version | `200` | App not answering |
| `GET /health/live` | Liveness | `200` `alive` | Process dead |
| `GET /health/ready` | Postgres + Redis | `200` `ready` | `503` if DB or Redis down |

```bash
# From the backend container
docker compose exec backend python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"
docker compose exec backend python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health/ready').read())"
```

Compose already healthchecks `/health/ready` on the `backend` service.

Details: [health.md](./health.md).

---

## Logs

### Where to look

| Concern | Service(s) | Command |
|---------|------------|---------|
| **API** | `backend` | `docker compose logs -f backend` |
| **Celery worker** (scans, reports, agent reconcile) | `celery-worker` | `docker compose logs -f celery-worker` |
| **Celery beat** (schedules) | `celery-beat` | `docker compose logs -f celery-beat` |
| **Nginx** | `nginx` | `docker compose logs -f nginx` |
| **Scanner / plugin execution** | `backend` (inline scans) or `celery-worker` (queued) | See below |
| **Monitoring agent ingest** | `backend` | `docker compose logs -f backend` (filter for monitoring / agent) |
| **Observability stack** | `prometheus`, `grafana`, `loki`, `promtail` | `docker compose logs -f grafana loki promtail prometheus` |

Convenience:

```bash
make logs              # all services
make backend-logs      # backend + celery-worker + celery-beat
```

### Scanner logs

Scan plugins run **inside** the API process when `SCAN_RUN_INLINE=true` (development default), or inside **Celery worker** when `SCAN_RUN_INLINE=false` (production default).

```bash
# Production / queued scans
docker compose logs -f celery-worker | findstr /i "scan plugin"

# Inline (dev)
docker compose logs -f backend | findstr /i "scan plugin"
```

On Linux/macOS use `grep -i` instead of `findstr /i`.

### Monitoring logs

| Layer | Where |
|-------|--------|
| Agent register / heartbeat / metrics | `backend` API logs |
| Offline / delayed reconcile | `celery-worker` + `celery-beat` |
| Host metrics dashboards | Grafana → http://localhost:${GRAFANA_PORT:-3000} |
| Aggregated container logs | Loki (via Promtail) if the monitoring stack is up |

---

## Restart

Restart one service without tearing down the stack:

```bash
docker compose restart <service>
```

Common services:

| Service | When to restart |
|---------|-----------------|
| `backend` | API hung, settings change that needs process reload (Compose also bind-mounts code in dev) |
| `celery-worker` | Queued scans/reports stuck; worker OOM |
| `celery-beat` | Schedules not firing |
| `nginx` | Proxy / static routing issues |
| `frontend` | UI not loading (dev Vite) |
| `postgres` | Only if necessary — prefer not; check connections first |
| `redis` | Rate-limit / Celery broker issues (ephemeral — safe to empty) |

Examples:

```bash
docker compose restart backend
docker compose restart celery-worker celery-beat
docker compose restart nginx
```

Recreate after image/env change:

```bash
docker compose up -d --force-recreate backend
```

Full stop (keeps volumes):

```bash
docker compose down
# or: make down
```

**Do not** use `docker compose down -v` on production — that deletes `postgres_data`.

---

## Migration

Always run against the live Compose backend (uses container env / Postgres):

```bash
make migrate
```

Equivalent:

```bash
docker compose exec backend alembic upgrade head
```

Check current revision:

```bash
docker compose exec backend alembic current
```

One step back (only if you know the risk):

```bash
make migrate-down
# docker compose exec backend alembic downgrade -1
```

**Before production upgrades:** take a Postgres backup ([backups.md](./backups.md)).

---

## Backup

### Create a database dump

```bash
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sandbox}" \
  -d "${POSTGRES_DB:-sandbox}" \
  -Fc \
  > "sandbox-$(date +%Y%m%d-%H%M%S).dump"
```

Encrypt and store offsite per [backups.md](./backups.md) (daily / 7-day retention / monthly restore test).

Optional report files:

```bash
tar -czf sandbox-reports-$(date +%Y%m%d).tar.gz -C backend storage/reports
```

Redis is **ephemeral** — do not treat Redis dumps as business recovery.

### Restore a database dump

```bash
docker compose stop backend celery-worker celery-beat

docker compose exec postgres psql -U sandbox -c "DROP DATABASE IF EXISTS sandbox;"
docker compose exec postgres psql -U sandbox -c "CREATE DATABASE sandbox;"

docker compose exec -T postgres pg_restore \
  -U sandbox \
  -d sandbox \
  --no-owner --no-acl \
  < sandbox-YYYYMMDD-HHMMSS.dump

docker compose start backend celery-worker celery-beat
docker compose exec backend alembic current
```

Full policy and data classification: [backups.md](./backups.md).

---

## Incident

Work top-down: health → logs → restart → config.

### Scans stop

1. `GET /health/ready` — Postgres and Redis up?
2. Asset gates — `website` / `domain` / `public_ip` must be **ownership-verified** and `status=active`.
3. Is Celery required?
   - Production: `SCAN_RUN_INLINE=false` → worker must run: `docker compose ps celery-worker`
4. Logs:
   ```bash
   docker compose logs --tail 200 celery-worker
   docker compose logs --tail 200 celery-beat   # scheduled scans
   ```
5. Restart worker/beat if hung: `docker compose restart celery-worker celery-beat`.
6. Check scan row status in API/UI (pending / queued / failed).

### AI stops

1. `OPENAI_API_KEY` set in `.env`? Empty key → chat/report summaries use offline / degraded path (by design).
2. Restart backend after changing the key: `docker compose restart backend`.
3. Logs: `docker compose logs --tail 200 backend` — look for AI / OpenAI / timeout errors.
4. Confirm caller has `ai:use` (viewers cannot use AI).
5. Network egress from `backend` to the model provider must be allowed.

### Database unavailable

1. `docker compose ps postgres` — healthy?
2. Readiness: `/health/ready` → `database: disconnected`.
3. Logs: `docker compose logs --tail 200 postgres backend`.
4. Credentials: `.env` `POSTGRES_*` must match the volume’s original password (changing password after first init does not update the volume).
5. Disk full on host / volume?
6. Do **not** `down -v` to “fix” — restore from backup instead.

### Celery stops

1. `docker compose ps celery-worker celery-beat redis`.
2. Redis ping: `docker compose exec redis redis-cli ping` → `PONG`.
3. Logs: `docker compose logs --tail 200 celery-worker celery-beat`.
4. Restart: `docker compose restart celery-worker celery-beat`.
5. If Redis was wiped: queues are empty (expected); re-queue failed scans/reports from the UI/API.
6. Only **one** `celery-beat` instance should run.

### SIEM stops receiving events

1. Audit still lands in Postgres first — check `GET /api/v1/audit-logs` (or DB) for new rows.
2. Config: `AUDIT_SIEM_SINK` (`none` | `syslog` | `splunk` | `elk` | `sentinel`) and sink-specific vars in `.env`.
3. Sink `none` means no export by design.
4. Logs: `docker compose logs --tail 200 backend` — logger `sandbox.audit.siem`; export failures are logged and **must not** fail the API.
5. Restart backend after SIEM env changes: `docker compose restart backend`.
6. Verify network from backend to SIEM endpoint (firewall, TLS, tokens).

### Quick triage table

| Symptom | First checks |
|---------|----------------|
| App blank on `:80` | `nginx`, `frontend`, `docker compose logs nginx frontend` |
| API 503 / not ready | Postgres, Redis, `/health/ready` |
| Login lockouts odd after Redis restart | Expected — lockout counters are ephemeral |
| Reports stuck `generating` | Same as scans — Celery when `REPORT_RUN_INLINE=false` |
| Grafana down | Optional; does not block the product |

More detail: [troubleshooting.md](./troubleshooting.md).
