# Installation

This guide walks through the **exact** local install path using Docker Compose. After these steps you will have a running app at http://localhost, an API at `/api/v1`, and the full observability stack (Prometheus, Grafana, Loki).

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| Git | To clone the repository |
| Docker Engine + Docker Compose v2 | `docker compose` (plugin), not legacy `docker-compose` |
| ~4 GB free RAM | All services together; you can stop monitoring if needed |
| Ports available | 80 (nginx), 5432 (Postgres), 6379 (Redis), 3000 (Grafana), 9090 (Prometheus), 3100 (Loki) |

No local Python or Node install is required for the Compose path — both run inside containers.

## Step 1 — Clone the repository

```bash
git clone <repository-url> sandbox
cd sandbox
```

You should see at minimum: `docker-compose.yml`, `.env.example`, `backend/`, `frontend/`, `Makefile`, and `infrastructure/`.

## Step 2 — Create environment file

```bash
cp .env.example .env
```

Edit `.env` before starting if you plan to run with `ENVIRONMENT=production` (see [production.md](./production.md)). For local development the example values work, but you **must** keep `SECRET_KEY` and `JWT_SECRET` at least 32 characters (the placeholders in `.env.example` already satisfy this).

### Important: `POSTGRES_HOST` in Compose

`.env.example` sets `POSTGRES_HOST=localhost` for running the backend **outside** Docker. When you use Compose, `docker-compose.yml` **overrides** this for backend and Celery services:

```yaml
POSTGRES_HOST: postgres
REDIS_URL: redis://redis:6379/0
```

So you do not need to change `POSTGRES_HOST` in `.env` for the Compose install — the override wins inside containers. Host tools (e.g. `psql` from your laptop) still use `localhost:5432` because Postgres publishes port 5432.

## Step 3 — Start the stack

```bash
docker compose up -d
```

Equivalent: `make up`.

### What happens when you run `docker compose up -d`

1. **Network** — Creates bridge network `sandbox` for inter-container DNS (`postgres`, `redis`, `backend`, etc.).

2. **Volumes** — Creates named volumes if they do not exist:
   - `postgres_data` — PostgreSQL data directory
   - `redis_data` — Redis persistence
   - `prometheus_data`, `grafana_data`, `loki_data` — observability storage
   - `frontend_node_modules` — cached npm modules for the dev frontend container

3. **Images** — Pulls public images (Postgres 16, Redis 7, nginx, Prometheus, Grafana, Loki, Promtail, exporters). Builds local images from:
   - `./backend` → used by `backend`, `celery-worker`, `celery-beat`
   - `./frontend` (target `dev`) → Vite dev server

4. **Startup order** (simplified):
   ```
   postgres, redis          → healthchecks must pass (pg_isready, redis-cli ping)
        ↓
   backend                  → uvicorn with --reload; readiness on /health/ready
        ↓
   celery-worker            → background scan/report jobs
        ↓
   celery-beat              → scheduled scans, agent offline reconcile
   frontend, nginx          → UI + reverse proxy (nginx waits on backend + frontend)
   prometheus, loki, …      → monitoring stack
   ```

5. **What does *not* run automatically**
   - **Database migrations** — schema is not applied until you run `make migrate`
   - **Demo seed data** — optional; run `make seed` after migrate
   - **TLS** — local dev uses HTTP on port 80; production HTTPS uses `docker-compose.edge.yml` (Caddy) — [tls-edge.md](./tls-edge.md)

6. **First boot timing** — Backend healthcheck allows ~15s start period. Until Postgres and Redis are healthy, backend readiness returns 503. Frontend Vite may take 30–60s on first `npm install` inside the container.

### Services and roles

| Service | Role |
|---------|------|
| `nginx` | Public entry on port 80; proxies `/api/` → backend, `/` → frontend |
| `backend` | FastAPI API on internal port 8000 |
| `frontend` | React + Vite dev server on internal port 5173 |
| `postgres` | Primary database |
| `redis` | Celery broker + cache |
| `celery-worker` | Async scans and reports (when not inline) |
| `celery-beat` | Cron-style schedules (e.g. due scan checks every minute) |
| `prometheus` / `grafana` / `loki` / `promtail` | Metrics and logs |
| `postgres-exporter` / `redis-exporter` | DB/Redis metrics for Prometheus |

Full service table: [docker.md](./docker.md).

## Step 4 — Apply database migrations

**Required** before using the product:

```bash
make migrate
```

Runs inside the backend container:

```bash
docker compose exec backend alembic upgrade head
```

This creates all tables, enums, indexes, and triggers (including audit log hash chain through migration `045`). Without this step, API calls that touch the database will fail.

Verify:

```bash
docker compose exec backend alembic current
```

Should show head revision `045_audit_log_hash_chain` (or later).

## Step 5 — Optional demo data

```bash
make seed
```

Creates organization **Demo Corp**, projects, assets, sample scans, and users documented in [demo-data.md](../demo-data.md).

Demo login after seed:

| Field | Value |
|-------|--------|
| Email | `owner@demo.sandbox` |
| Password | `DemoPassword1!` |

## Step 6 — Verify the install

| Check | Command / URL | Expected |
|-------|----------------|----------|
| Container health | `docker compose ps` | `backend` shows `healthy` when Postgres + Redis are up |
| Backend readiness | See command below | JSON with `"status":"ready"` |
| App UI | http://localhost | Login / register page |
| API | http://localhost/api/v1/... | JSON responses (401 without auth is OK) |
| OpenAPI | http://localhost/docs | Swagger UI (only when `ENVIRONMENT` ≠ `production`) |
| Grafana | http://localhost:3000 | Login with `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` from `.env` |

Health endpoints live on the backend root (`/health/ready`), not under `/api/v1`. Nginx does not proxy `/health` to the host — check readiness inside the backend container:

```bash
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health/ready').read())"
```

All services should show `healthy` or `running` in `docker compose ps`.

## Request flow (after install)

```
Browser → http://localhost:80 (nginx)
            ├─ /api/*     → backend:8000 (FastAPI)
            ├─ /docs      → backend:8000 (non-production only)
            └─ /*         → frontend:5173 (Vite dev)
```

Org-scoped API calls require:

- `Authorization: Bearer <access_token>`
- `X-Organization-ID: <uuid>`

## Makefile shortcuts

| Command | Action |
|---------|--------|
| `make up` | `docker compose up -d` |
| `make down` | Stop and remove containers (volumes kept) |
| `make build` | Rebuild backend/frontend images |
| `make migrate` | Alembic upgrade head |
| `make seed` | Demo tenant |
| `make logs` | Follow all service logs |
| `make backend-logs` | Backend + Celery logs |
| `make shell` | Bash in backend container |
| `make test` | Backend pytest (runs on host, not in Compose) |

## Next steps

- [configuration.md](./configuration.md) — every environment variable
- [production.md](./production.md) — hardening and production gates
- [backups.md](./backups.md) — what to back up (manual procedures)
- [troubleshooting.md](./troubleshooting.md) — common failures
