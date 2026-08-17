# Backend

FastAPI app in `backend/app/`. API version string: `1.0.0` (`app.core.version`). HTTP prefix: `/api/v1`.

## Layout

Feature modules own models, schemas, routers, services, repositories:

`auth`, `users`, `organizations`, `members`, `projects`, `assets`, `scans`, `findings`, `risk`, `reports`, `ai`, `audit`, `monitoring`, plus `plugins`, `jobs`, `events`, `core`.

Shared pieces: `app/shared/`, `app/core/` (config, DB, permissions, logging, health), `app/middleware/`.

## Router mount (`app/api/v1/router.py`)

| Prefix | Module |
|--------|--------|
| `/auth` | Auth |
| `/users` | Users |
| `/organizations` | Orgs, dashboard, activity, current reports, risk, current monitoring, current audit-logs |
| `/organizations/ai` | AI chat |
| `/organizations` (members router) | Members / invites |
| `/projects` | Projects (nested assets, scans, findings, reports, monitoring enroll) |
| `/monitoring` | Agent install/register/heartbeat (agent credentials) |
| `/audit-logs` | Org-scoped audit search (user JWT + org header) |

Health routes are on the app root, not under `/api/v1`: `/health`, `/health/live`, `/health/ready`. Prometheus: `/metrics`.

## Request stack (`app.main`)

1. Lifespan: `ensure_default_handlers()` on the event bus
2. Security headers
3. Request context (request/correlation IDs)
4. CORS (methods GET/POST/PUT/PATCH/DELETE/OPTIONS; headers include `Authorization`, `X-Organization-ID`, `X-Session-ID`)
5. SlowAPI rate limit
6. Request logging
7. Feature routers

OpenAPI UI is off in production.

## Scan and risk engines

- Scan: `app/core/scan_engine/` (orchestrator, adapter). Plugins: `app/plugins/`.
- Risk: `app/core/risk_engine/` + `app/risk/` models. Rule specs also in `app/core/rule_engine/`.
- AI: `app/ai/` HTTP + `app/services/ai/` LLM; `app/core/ai_engine/` and `app/core/report_engine/` for summaries.

## Persistence

SQLAlchemy models, Alembic in `backend/alembic/`. Head revision at the time of this doc: **`045_audit_log_hash_chain`**. Tests typically use SQLite `create_all` rather than Alembic.

## Config

`app/core/config.py` via environment / `.env`. See [deployment/environment](../deployment/environment.md).
