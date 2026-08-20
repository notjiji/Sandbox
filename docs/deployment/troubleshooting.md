# Troubleshooting

Common issues when installing and running Sandbox with Docker Compose. For health probe details see [health.md](./health.md).

## Install and startup

### `docker compose up` fails immediately

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Port already allocated | Another service on 80, 5432, 6379, 3000, etc. | Change `NGINX_PORT` / stop conflicting service / `docker compose ps` on another project |
| Cannot connect to Docker daemon | Docker not running | Start Docker Desktop or `systemctl start docker` |
| Build fails on backend | Network or pip timeout | Retry `docker compose build`; check proxy settings |

### Backend container exits on start

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `SECRET_KEY must be at least 32 characters` | Short secrets in `.env` | Lengthen `SECRET_KEY` and `JWT_SECRET` |
| Production validator error | `ENVIRONMENT=production` with example secrets | Use real secrets; set `RESEND_API_KEY` — see [production.md](./production.md) |
| Database connection refused | Postgres not ready yet | Wait for postgres healthcheck; `docker compose ps` |

Check logs:

```bash
docker compose logs backend --tail 100
```

### Backend unhealthy / readiness 503

Readiness requires **both** Postgres and Redis:

```bash
docker compose exec backend python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health/ready').read())"
```

| `database` | Fix |
|------------|-----|
| `disconnected` | Check postgres logs; verify `POSTGRES_*` credentials match; ensure migrations not required for connection itself |
| `redis` disconnected | Check redis container; verify `REDIS_URL=redis://redis:6379/0` inside Compose |

## Database and migrations

### API errors: relation does not exist / column does not exist

**Cause:** Migrations not applied.

```bash
make migrate
# or
docker compose exec backend alembic upgrade head
```

### `alembic upgrade head` fails

| Error type | Fix |
|------------|-----|
| Password authentication failed | `.env` `POSTGRES_PASSWORD` must match postgres container env; recreate volume if you changed password after first init |
| Enum / migration conflict | Check [database/migrations.md](../database/migrations.md); may need fresh volume in dev: `docker compose down -v` (**destroys data**) |
| Connection to localhost refused from backend container | Should use `POSTGRES_HOST=postgres` — Compose overrides; if running alembic on host, use `POSTGRES_HOST=localhost` |

### Changed `POSTGRES_PASSWORD` but login still fails

Postgres initializes password only on **first** volume creation. Either:

- Restore password inside postgres: `ALTER USER sandbox PASSWORD 'newpass';`
- Or reset dev data: `docker compose down -v` and start fresh (**data loss**)

## Application behavior

### http://localhost shows blank or connection refused

1. `docker compose ps` — nginx, frontend, backend running?
2. Frontend first boot runs `npm install` — wait 1–2 minutes; `docker compose logs frontend`
3. Hard refresh browser; check nginx logs: `docker compose logs nginx`

### API returns 401 on all org routes

Expected without login. Org-scoped routes need:

```
Authorization: Bearer <access_token>
X-Organization-ID: <uuid>
```

Missing `X-Organization-ID` returns 401 even with valid JWT.

### CORS errors from browser (dev on port 5173)

Add your origin to `CORS_ORIGINS` in `.env`:

```
CORS_ORIGINS=http://localhost:5173,http://localhost:80,http://127.0.0.1:5173
```

Restart backend after change.

### Registration email / OTP never arrives

| Environment | Behavior |
|-------------|----------|
| Development, empty `RESEND_API_KEY` | Email not sent; use `make seed` for pre-verified demo users or verify users in DB |
| Production | Startup fails without `RESEND_API_KEY` |

Check Resend dashboard for bounces; verify `RESEND_FROM` domain is authorized.

### Scans stay pending / never complete

| Cause | Fix |
|-------|-----|
| `ENVIRONMENT=production` or `SCAN_RUN_INLINE=false` | Celery worker must run: `docker compose ps celery-worker` |
| Worker crashed | `docker compose logs celery-worker` |
| Asset not verified | `website`, `domain`, `public_ip` require ownership verification before scan |
| Asset not active | Asset `status` must be `active` |

### Reports stuck in generating

Same pattern as scans — check `REPORT_RUN_INLINE` and celery-worker logs.

### Scheduled scans never fire

Requires **celery-beat** running:

```bash
docker compose ps celery-beat
docker compose logs celery-beat
```

Beat task `check_due_schedules` runs every minute.

## Monitoring stack

### Grafana login fails

Default from `.env.example`: `admin` / `admin`. Change via `GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` — only applies on **first** Grafana volume init; otherwise reset through Grafana UI or delete `grafana_data` volume (loses custom dashboards).

### Prometheus / Grafana empty

Scrape targets are pre-provisioned for Compose service names. If you renamed services or run partial stack, targets may be down — check Prometheus → Status → Targets at http://localhost:9090.

### Promtail not shipping logs (Linux vs Windows)

Promtail mounts `/var/run/docker.sock`. On Docker Desktop for Windows/Mac, behavior differs; logs may still appear via `docker compose logs`.

## Performance and resources

### High memory use

Full stack runs 12+ containers. Stop monitoring if not needed:

```bash
docker compose stop prometheus grafana loki promtail redis-exporter postgres-exporter
```

### Slow scans

Plugins perform real HTTP/DNS/TLS against targets. Timeouts are per-plugin; worker CPU and network matter. Nmap optional in backend image for port plugin.

## Useful diagnostic commands

```bash
# Service status
docker compose ps

# All logs
docker compose logs -f

# Backend shell
make shell

# DB shell
docker compose exec postgres psql -U sandbox -d sandbox

# Redis ping
docker compose exec redis redis-cli ping

# Current migration
docker compose exec backend alembic current

# Run backend tests (on host)
make test
```

## Getting help

1. Reproduce with logs from failing service
2. Confirm `make migrate` applied and `ENVIRONMENT` matches expectations
3. Check [known-limits.md](../security/known-limits.md) for intentional product gaps
4. Review [installation.md](./installation.md) step-by-step

If the issue is data loss, see [backups.md](./backups.md) — there is no in-app restore.
