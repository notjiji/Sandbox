# Sandbox

Multi-tenant security assessment platform: inventory assets, run plugin scans, review findings, score risk, report, optional server monitoring and org-scoped AI.

**Documentation source of truth:** [docs/README.md](docs/README.md) — especially `docs/product/`, `docs/architecture/`, `docs/database/`, `docs/security/`, `docs/testing/`, `docs/deployment/`, and `docs/roadmap/`. Those pages describe the **current code**, not a wishlist.

## Stack

- Backend: FastAPI (`/api/v1`), PostgreSQL, Redis, Celery
- Frontend: React + TypeScript + Vite + Tailwind
- Local runtime: Docker Compose (nginx, Prometheus, Grafana, Loki)

## Quick start

```bash
cp .env.example .env   # set secrets (≥32 chars)
make up
make migrate
make seed
```

Open http://localhost — demo owner `owner@demo.sandbox` / `DemoPassword1!` (see [docs/demo-data.md](docs/demo-data.md)).

Org-scoped API calls need `Authorization: Bearer` and `X-Organization-ID`.
