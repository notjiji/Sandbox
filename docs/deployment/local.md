# Local setup

## Prerequisites

Docker Compose, a `.env` copied from `.env.example` with secrets ≥ 32 characters.

## Bring the stack up

```bash
make up          # docker compose up -d
make migrate     # alembic upgrade head
make seed        # optional demo tenant — see docs/demo-data.md
```

Other targets: `make down`, `make build`, `make logs`, `make backend-logs`, `make shell`, `make monitoring`, `make test`.

## URLs (Compose defaults)

| What | Where |
|------|--------|
| App (nginx) | http://localhost (`NGINX_PORT`, default 80) |
| API via nginx | http://localhost/api/v1 |
| OpenAPI (non-production) | Backend `/docs` (through nginx or backend container port if exposed — Compose **exposes** backend 8000 internally only; use nginx) |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Loki | http://localhost:3100 |
| Postgres | localhost:`POSTGRES_PORT` (default 5432) |
| Redis | localhost:6379 |

Demo login: `owner@demo.sandbox` / `DemoPassword1!` after seed.

## Frontend without Compose

Vite: `npm run dev` in `frontend/` (port 5173). Point `VITE_API_BASE_URL` at the API. CORS defaults include `http://localhost:5173`.
