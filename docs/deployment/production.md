# Production deployment

Production uses **`docker-compose.prod.yml`**: baked images (no bind mounts), static frontend, multi-worker API, Celery workers, and an internal app nginx.

**Public HTTPS (recommended):** add **`docker-compose.edge.yml`** — Caddy terminates TLS on `:443` and forwards to nginx. See [tls-edge.md](./tls-edge.md).

```bash
cp .env.production.example .env
# edit secrets, EDGE_DOMAIN, ACME_EMAIL, and HTTPS URLs
docker compose -f docker-compose.prod.yml -f docker-compose.edge.yml run --rm migrate
docker compose -f docker-compose.prod.yml -f docker-compose.edge.yml up -d --build
```

Without the edge overlay, nginx may bind HTTP only (`NGINX_HTTP_PORT`) — suitable for localhost or when you terminate TLS with an external proxy.

Development remains **`docker-compose.yml`** (hot reload, Vite, exposed Postgres/Redis/Grafana for local debugging).

## Production gates (enforced in code)

When `ENVIRONMENT=production`, `Settings.validate_production_settings` in `backend/app/core/config.py` runs at startup. The API **will not start** if any check fails:

| Check | Requirement |
|-------|-------------|
| Debug | `DEBUG=false`, `LOG_LEVEL` not `DEBUG` |
| Secrets | Strong `SECRET_KEY`, `JWT_SECRET`, `BACKUP_ENCRYPTION_PASSPHRASE` (no placeholders, min 32 chars) |
| Database | Strong `POSTGRES_PASSWORD`; `POSTGRES_USER` not `postgres`/`admin`/`root` |
| Email | Non-placeholder `RESEND_API_KEY` |
| Public URLs | `FRONTEND_URL`, `PUBLIC_API_URL`, and `CORS_ORIGINS` use **HTTPS** and not localhost |
| Background jobs | `SCAN_RUN_INLINE=false`, `REPORT_RUN_INLINE=false` |
| AI | `AI_ENABLED=true` requires `OPENAI_API_KEY`; use `AI_ENABLED=false` for assessment-only |
| Reports (S3) | `REPORT_S3_BUCKET` when `REPORT_STORAGE_BACKEND=s3` |

Additionally enforced by defaults (not validator errors):

| Behavior | Production |
|----------|------------|
| OpenAPI `/docs`, `/redoc`, `/openapi.json` | Disabled at app + nginx public edge |
| Prometheus `/metrics` | Not on public edge (nginx 404); internal scrape `backend:8000/metrics` |
| `SCAN_RUN_INLINE` | `false` unless explicitly set |
| `REPORT_RUN_INLINE` | `false` unless explicitly set |

Scans and reports then require a running **Celery worker** and **Redis**.

## Recommended production architecture

```
User
 │  HTTPS :443
 ▼
Caddy (docker-compose.edge.yml — TLS, ACME, redirect)
 │
 │  HTTP (internal Docker network)
 ▼
nginx  —  /api → backend, / → frontend (static)
 │
 ├── backend ── celery-worker / celery-beat
 └── postgres + redis (internal only)
```

Compose: `docker-compose.prod.yml` + `docker-compose.edge.yml`. Env: `.env.production.example`. Guide: [tls-edge.md](./tls-edge.md).

Alternative: terminate TLS with Traefik, host nginx, or a cloud load balancer — forward HTTP to `NGINX_HTTP_PORT=127.0.0.1:8080` with `X-Forwarded-Proto: https`.

Observability (Prometheus, Grafana, Loki) is **not** included in the production compose file. Run a separate stack or bind monitoring to the internal network only.

## Minimum production checklist

### Application

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Generate strong random `SECRET_KEY` and `JWT_SECRET` (≥ 32 chars, not example prefixes)
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set `RESEND_API_KEY` and verified `RESEND_FROM` domain
- [ ] Set `FRONTEND_URL` to public HTTPS origin
- [ ] Set `PUBLIC_API_URL` to public API base (e.g. `https://app.example.com/api/v1`)
- [ ] Restrict `CORS_ORIGINS` to your frontend origin(s) only
- [ ] Run `alembic upgrade head` before serving traffic
- [ ] Confirm Celery worker and beat containers are healthy

### Infrastructure

- [ ] TLS on public edge — `docker-compose.edge.yml` (Caddy) or external proxy — [tls-edge.md](./tls-edge.md)
- [ ] Firewall: expose only **443** (and **80** for ACME redirect); do not expose Postgres/Redis publicly
- [ ] Change Grafana default admin password or disable public Grafana access
- [ ] Set `BACKUP_ENCRYPTION_PASSPHRASE` and verify backup service is running (`docker compose ps backup`)
- [ ] Postgres backups per [backups.md](./backups.md): daily dump (automated), 7-day retention, encrypted `backup_storage` volume, monthly restore test
- [ ] Report file directory backed up or accepted as regenerable
- [ ] `.env` / secrets in a vault (not only on the app host)
- [ ] Do **not** rely on Redis dumps for disaster recovery
- [ ] Secret storage (vault, cloud secret manager) instead of plain `.env` on disk
- [ ] Log and metric retention policy

### Security

- [ ] Do not commit `.env` or real secrets to git
- [ ] Rotate JWT/app secrets on compromise (invalidates all sessions)
- [ ] Review [security/known-limits.md](../security/known-limits.md) — no API keys product, operator-trust scanning model, etc.
- [ ] Optional: configure `AUDIT_SIEM_SINK` for audit log export

## Frontend for production

The Compose file builds frontend with target `dev` (Vite hot reload). For production UI:

1. Build static assets: `frontend/Dockerfile` target `production` (nginx serving `/dist`)
2. Either replace the `frontend` service image/target or serve static files from your edge nginx
3. Ensure `VITE_API_BASE_URL=/api/v1` (or full API URL if cross-origin)

Cross-origin API requires correct `CORS_ORIGINS` and HTTPS cookies if you add cookie-based auth later.

## Backend command

Development Compose uses:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Production should use **no reload**, multiple workers if needed, and a process manager:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or gunicorn with uvicorn workers — not defined in-repo; operator choice.

## Scaling notes

| Component | In-repo default | Scale approach |
|-----------|-----------------|----------------|
| API (`backend`) | 1 container | Horizontal replicas behind load balancer; shared Postgres/Redis |
| Celery worker | 1 container | Add workers; same Redis broker |
| Celery beat | **Must be 1** | Only one beat scheduler |
| Postgres | 1 container | Managed RDS/Cloud SQL or Patroni — not documented here |
| Redis | 1 container | Managed Redis or Sentinel — not documented here |

No HA or multi-region guide is included in this codebase.

## Health checks for orchestrators

Use these paths on the backend (port 8000 internally):

| Path | Use |
|------|-----|
| `GET /health/live` | Liveness — process responding |
| `GET /health/ready` | Readiness — Postgres + Redis connected |

Compose already healthchecks `/health/ready` on the backend container.

## What this repository does not provide

- Multi-node Postgres HA or managed cloud wiring (operator choice beyond Compose)
- Database point-in-time recovery beyond [backups.md](./backups.md)
- WAF, DDoS protection, or IP allowlists
- Automated **deploy** pipelines (CI **quality gate** exists — [ci.md](./ci.md))
- Secret rotation runbooks
- Kubernetes manifests

Caddy + Let's Encrypt **is** included via `docker-compose.edge.yml` for single-server deployments. Cloud load balancers and Traefik remain valid alternatives — see [tls-edge.md](./tls-edge.md).

## Staging

Use `ENVIRONMENT=staging` to keep OpenAPI enabled while testing production-like settings. The production validator runs only when `ENVIRONMENT=production`. Staging still defaults `SCAN_RUN_INLINE`/`REPORT_RUN_INLINE` based on environment name (`false` for staging unless overridden).

Related: [production-runbook.md](./production-runbook.md) (day-2 ops), [configuration.md](./configuration.md), [installation.md](./installation.md), [troubleshooting.md](./troubleshooting.md).
