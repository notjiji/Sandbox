# Docker Compose (as built)

File: `docker-compose.yml`. Network: `sandbox`.

| Service | Image / build | Notes |
|---------|---------------|--------|
| postgres | postgres:16-alpine | Volume `postgres_data`; health `pg_isready` |
| redis | redis:7-alpine | Volume `redis_data` |
| backend | `./backend` | `uvicorn app.main:app --reload`; env from `.env` + Compose overrides |
| celery-worker | same image | `celery -A app.workers.celery_app worker` — healthcheck via `python -m app.workers.health worker` |
| celery-beat | same image | beat scheduler — **exactly one replica**; healthcheck via `python -m app.workers.health beat` |
| frontend | `./frontend` target `dev` | Vite; `VITE_API_BASE_URL=/api/v1` |
| nginx | nginx:1.27-alpine | Config `infrastructure/nginx/nginx.conf` |
| prometheus | prom/prometheus:v2.55.1 | |
| grafana | grafana/grafana:11.4.0 | Provisioning under `infrastructure/monitoring/grafana` |
| loki | grafana/loki:3.3.2 | |
| promtail | grafana/promtail:3.3.2 | Docker socket |
| redis-exporter | oliver006/redis_exporter | |
| postgres-exporter | prometheuscommunity/postgres-exporter | |

Backend and workers mount `./backend:/app` (live code). Frontend mounts `./frontend` plus an anonymous `frontend_node_modules` volume.

This is a **development Compose file** (reload, default Grafana password, bind-mounted source). It is not by itself a hardened production topology.

## Production (`docker-compose.prod.yml` + optional `docker-compose.edge.yml`)

| Service | Notes |
|---------|--------|
| `caddy` | Edge overlay only — public `:443`/`:80`, automatic TLS — [tls-edge.md](./tls-edge.md) |
| `nginx` | Internal app router; config `infrastructure/nginx/nginx.prod.conf` |
| `backend`, `celery-worker`, `celery-beat`, `frontend`, `backup` | No public ports |
| `postgres`, `redis` | Internal network only |
