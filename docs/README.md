# Sandbox Platform Documentation

Technical documentation for the Sandbox security assessment platform.

## Feature documentation

| Area | Description |
|------|-------------|
| [Reports](./reports/README.md) | PDF report generation, templates, API |
| [Dashboard](./dashboard/README.md) | Security Intelligence dashboard |
| [RBAC](./rbac/README.md) | Roles, permissions, enforcement |
| [Scan engine & plugins](./plugins/README.md) | Scanner orchestration and plugin development |
| [Auth](./auth/README.md) | Registration, login, sessions, tokens |
| [Organizations](./organizations/README.md) | Multi-tenancy, settings, activity |
| [Findings](./findings/README.md) | Normalized security findings |
| [Risk](./risk/README.md) | Scoring, grades, trends |
| [AI Assistant](./ai/README.md) | Org-scoped chat and context |
| [Audit](./audit/README.md) | Audit log and event catalog |
| [Background jobs](./jobs/README.md) | Celery workers and scheduled tasks |
| [Scans](./scans/README.md) | Scan lifecycle and schedules (see also [scan-engine.md](./scan-engine.md)) |

## Existing deep-dive docs

| Document | Description |
|----------|-------------|
| [scan-engine.md](./scan-engine.md) | Full scan orchestrator, asset adapter, lifecycle |
| [demo-data.md](./demo-data.md) | Seed script and demo accounts |

## Diagrams

Auth flow diagrams live in [diagrams/](./diagrams/):

- Register flow, login flow, token lifecycle, auto-refresh, RBAC enforcement

## Architecture placeholders

Reserved for future expansion:

- `docs/architecture/` — system-wide diagrams
- `docs/api/` — OpenAPI supplements
- `docs/database/` — ERD and migration guides

## Quick links (code)

| Layer | Path |
|-------|------|
| Backend API | `backend/app/api/v1/router.py` |
| Permissions | `backend/app/core/permissions.py` |
| Scan engine | `backend/app/core/scan_engine/` |
| Plugins | `backend/app/plugins/` |
| Frontend routes | `frontend/src/app/routes/index.tsx` |

## Local development

```bash
make up          # Start Docker services
make migrate     # Run Alembic migrations
make seed        # Load demo data (see demo-data.md)
```

Interactive API docs: `http://localhost:8000/docs` (non-production).
