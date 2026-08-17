# Non-functional requirements (as built)

These are constraints the **code and Compose stack actually implement**. Unpublished numbers are labeled as such.

## Authentication and security

- JWT access + hashed refresh; OTP email verify; lockout; password hashing.
- CORS allowlist from `CORS_ORIGINS`. Credentials allowed when `CORS_ALLOW_CREDENTIALS` is true.
- Security headers middleware. Rate limits: `RATE_LIMIT_DEFAULT` (100/minute) and `RATE_LIMIT_AUTH` (10/minute).
- OpenAPI `/docs` and `/redoc` are **disabled when `ENVIRONMENT=production`**.
- Production refuses default `SECRET_KEY` / `JWT_SECRET` / `changeme` Postgres password, and requires `RESEND_API_KEY`.
- Details: [security](../security/README.md).

## Multi-tenancy

- Tenant = `organizations` row. Data is scoped by `organization_id` (and project where relevant).
- Membership must be active. Isolation is enforced in services/repositories, not by a separate database per tenant.
- Tests: `backend/tests/test_org_isolation.py`.
- Details: [security/multi-tenancy](../security/multi-tenancy.md).

## RBAC

- Five org roles mapped to `Permission` enum values. Routes use `require_permission(...)`.
- There is no separate “system admin” product role in the UI; `users.is_superuser` exists on the model.
- Details: [security/rbac](../security/rbac.md).

## Performance

- **No published latency or throughput SLA** in this repo.
- What exists: SlowAPI rate limits; nginx `client_max_body_size 20m`; Celery offloads scans/reports when not inline; Redis as broker/cache; Prometheus metrics at `/metrics`.
- Scan duration depends on plugins, network, and optional Nmap — not bounded in config beyond plugin timeouts.

## Extensibility

- Scanner plugins implement `ScannerPlugin` / `ScannerPipeline` and register in `PluginLoader.BUILTIN_PLUGIN_CLASSES`.
- Scan profiles map to plugin slug lists (`backend/app/scans/profiles.py`).
- Domain events go through `event_bus.publish`; new subscribers can be added without changing publishers.
- Future plugins live under `backend/app/plugins/future/` with `enabled=False` except CVE.

## Deployment

- Local/dev path is Docker Compose: Postgres 16, Redis 7, API, Celery worker/beat, Vite frontend, nginx, Prometheus, Grafana, Loki, Promtail, exporters.
- Commands: `make up`, `make migrate`, `make seed`, `make test`.
- Health: `/health`, `/health/live`, `/health/ready` (DB + Redis).
- **No backup job or documented restore procedure.**
- Details: [deployment](../deployment/README.md).

## Logging and observability

- Structured application logs (`LOG_LEVEL`). Request logging middleware. Nginx JSON access logs.
- Prometheus scrapes the API and exporters. Grafana is provisioned. Loki + Promtail for container logs.
- Default Grafana admin is `admin` / `admin` unless env overrides — **dev default, not a production control**.
- Audit log is an application audit trail, not a substitute for infrastructure logs.

## Reliability of audit writes

- Audit persist uses a SAVEPOINT / fail-safe path: a failed audit write must not fail the business action.
- Hash chain is per organization. Rows without hashes (pre-migration) are skipped on verify.
- Immutability trigger is **PostgreSQL**. SQLite test DBs do not have that trigger.
