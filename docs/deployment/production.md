# Production deployment

The repository ships a **development-oriented** `docker-compose.yml`: bind-mounted source, uvicorn `--reload`, default Grafana credentials, and plain HTTP on port 80. Production deployment means satisfying the application's production validator and adding infrastructure this repo does **not** provide (TLS, backups, secret management, hardened images).

There is no separate production Compose overlay or Kubernetes chart in this repository.

## Production gates (enforced in code)

When `ENVIRONMENT=production`, `Settings.validate_production_settings` in `backend/app/core/config.py` runs at startup. The API **will not start** if any check fails:

| Check | Requirement |
|-------|-------------|
| Secrets | `SECRET_KEY` and `JWT_SECRET` must **not** start with `change-me` |
| Database password | `POSTGRES_PASSWORD` must **not** contain `changeme` (any case) |
| Email | `RESEND_API_KEY` must be set |

Additionally enforced by defaults (not validator errors):

| Behavior | Production |
|----------|------------|
| OpenAPI `/docs`, `/redoc` | Disabled |
| `SCAN_RUN_INLINE` | `false` unless explicitly set |
| `REPORT_RUN_INLINE` | `false` unless explicitly set |

Scans and reports then require a running **Celery worker** and **Redis**.

## Recommended production architecture

```
                    ┌─────────────┐
   Internet ───────►│ TLS proxy   │  (you provide: Caddy, Traefik, ALB, etc.)
                    │ (HTTPS)     │
                    └──────┬──────┘
                           │ HTTP to nginx :80
                    ┌──────▼──────┐
                    │ nginx       │  /api → backend, / → frontend static
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      backend         celery-worker    celery-beat
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    postgres + redis
```

Observability (Prometheus, Grafana, Loki) is optional but recommended for operations.

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

### Infrastructure (outside repo)

- [ ] TLS certificate and termination in front of nginx
- [ ] Firewall: expose only 443 (and admin paths if needed); do not expose Postgres/Redis publicly
- [ ] Change Grafana default admin password or disable public Grafana access
- [ ] Postgres backups per [backups.md](./backups.md): daily dump, 7-day retention, encrypted offsite storage, monthly restore test
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

- Production Compose/Kubernetes manifests
- TLS certificates or Let's Encrypt automation
- Database backups or point-in-time recovery
- WAF, DDoS protection, or IP allowlists
- CI/CD deploy pipelines
- Secret rotation runbooks

Those are operator responsibilities. [backups.md](./backups.md) documents manual backup procedures you can run until automated jobs exist.

## Staging

Use `ENVIRONMENT=staging` to keep OpenAPI enabled while testing production-like settings. The production validator runs only when `ENVIRONMENT=production`. Staging still defaults `SCAN_RUN_INLINE`/`REPORT_RUN_INLINE` based on environment name (`false` for staging unless overridden).

Related: [production-runbook.md](./production-runbook.md) (day-2 ops), [configuration.md](./configuration.md), [installation.md](./installation.md), [troubleshooting.md](./troubleshooting.md).
