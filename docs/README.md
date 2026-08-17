# Sandbox Platform Documentation

**Source of truth for the current implementation** is the seven folders below. They describe what the code does now (Alembic head `045_audit_log_hash_chain`), not a target playlist.

If a feature README disagrees with those folders, **the seven folders win** until the deep-dive is updated.

## Current implementation (start here)

| Folder | What it answers |
|--------|-----------------|
| [product/](./product/README.md) | Goal, users, use cases, in-vs-later, functional and non-functional as-built |
| [architecture/](./architecture/README.md) | System, backend, frontend, scan, AI, events, observability |
| [database/](./database/README.md) | ER diagram, tables, migrations |
| [security/](./security/README.md) | Auth, RBAC, tenancy, scanner limits, audit integrity |
| [testing/](./testing/README.md) | How tests run, what exists, gaps |
| [deployment/](./deployment/README.md) | Compose, env vars, health, production gates — **no backup story** |
| [roadmap/](./roadmap/README.md) | Limitations and later work (not shipped) |

## Feature deep-dives

Implementation notes for modules. Use them for APIs and internals; do not treat them as the product spec if they conflict with the folders above.

| Area | Description |
|------|-------------|
| [Auth](./auth/README.md) | Registration, login, sessions, tokens |
| [RBAC](./rbac/README.md) | Roles and permission matrix |
| [Organizations](./organizations/README.md) | Multi-tenancy, settings, activity |
| [Findings](./findings/README.md) | Normalized security findings |
| [Risk](./risk/README.md) | Scoring, grades, trends |
| [AI Assistant](./ai/README.md) | Org-scoped chat and context |
| [Audit](./audit/README.md) | Audit log and [event catalog](./audit/event-catalog.md) |
| [Reports](./reports/README.md) | PDF generation |
| [Dashboard](./dashboard/README.md) | Security Intelligence dashboard |
| [Scans](./scans/README.md) | Scan lifecycle and schedules |
| [Scan engine](./scan-engine.md) | Orchestrator, adapter, plugins |
| [Plugins](./plugins/README.md) | Scanner plugins and [authoring](./plugins/authoring.md) |
| [Monitoring](./monitoring/README.md) | Server agent, metrics, alerts |
| [Background jobs](./jobs/README.md) | Celery workers and beat |
| [Demo data](./demo-data.md) | Seed script and demo accounts |

Auth flow PNGs: [diagrams/](./diagrams/).

## Local development

```bash
make up          # Start Docker services
make migrate     # Alembic to head
make seed        # Demo tenant (see demo-data.md)
make test        # Backend pytest
```

App: `http://localhost` (nginx). OpenAPI: non-production only (`/docs` on the API). Grafana: `http://localhost:3000`.
