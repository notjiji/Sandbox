# ADR-001 — Why FastAPI

- **Status:** Accepted
- **Date:** 2026-08

## Context

The platform needs a typed HTTP API for a multi-tenant security product: auth, CRUD, long-running scans, OpenAPI for clients, and easy integration with SQLAlchemy and background workers.

## Decision

Use **FastAPI** (ASGI) as the sole API framework for `backend/app`.

## Why

- Native Pydantic models align with our request/response schemas and settings.
- Automatic OpenAPI (`/docs`) accelerates frontend and operator integration in non-production.
- Async-capable ASGI stack fits nginx → uvicorn without inventing a custom server layer.
- Strong dependency-injection pattern (`Depends`) maps cleanly to RBAC and org membership checks.
- Python ecosystem matches scanner plugins (HTTPX, dnspython, cryptography, Celery).

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Django + DRF | Heavier ORM/admin assumptions; less natural for a plugin scan engine |
| Flask | Weaker built-in typing/OpenAPI story |
| NestJS / Go | Would split language from plugin tooling already chosen in Python |
| Pure Starlette | Lose FastAPI’s schema/OpenAPI ergonomics for little gain |

## Consequences

- One Python backend owns API + plugins + workers’ shared libraries.
- OpenAPI is disabled in `ENVIRONMENT=production` by design.
- Team must stay disciplined about modular packages inside one FastAPI app (see ADR-010).
