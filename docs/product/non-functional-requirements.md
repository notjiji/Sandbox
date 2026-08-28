# Non-Functional Requirements

**Product:** Sandbox — Security Intelligence Platform  
**Release:** V1 (as built in this repository)  
**Status:** Source of truth for *how* the product must behave (security, performance, scale, availability, maintainability)  
**Related:** [Definition](./definition.md) · [Functional requirements](./functional-requirements.md) · [Security](../security/README.md) · [Deployment](../deployment/README.md) · [Testing](../testing/README.md)

Functional requirements (`FR-*`) say what the product does. This document says **constraints and quality targets**. Numbers below are either **enforced in code/config** or **design intent** for a single Compose stack. They are not a hosted-SaaS SLA. There is **no** published 99.9% uptime, p99 latency, or throughput contract in this repo — do not invent one.

## How to read this document

| Convention | Meaning |
|------------|---------|
| **ID** | Stable identifier (`NFR-<AREA>-<nn>`). |
| **Shall** | Mandatory V1 constraint. |
| **Kind** | `Enforced` = implemented in code or config. `Intent` = reasonable target for this architecture, not load-tested. `Explicitly unspecified` = do not assume a number. |
| **Notes** | Defaults and pointers. |

---

## 1. Security

### 1.1 Password hashing

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-01** | The system shall never store passwords in plaintext. | Enforced | Column `users.hashed_password`. |
| **NFR-SEC-02** | The system shall hash new passwords with Argon2 (`time_cost=3`, `memory_cost=65536`, `parallelism=4`, `hash_len=32`, `salt_len=16`). | Enforced | `backend/app/core/security.py`. |
| **NFR-SEC-03** | The system shall still verify legacy bcrypt hashes (`$2a$` / `$2b$` / `$2y$`) so existing rows are not locked out. | Enforced | Verify only; new hashes are Argon2. |
| **NFR-SEC-04** | New passwords shall be 12–128 characters and include uppercase, lowercase, a digit, and a special character. | Enforced | `PASSWORD_MIN_LENGTH=12`. Org settings may record a min-length preference; registration uses the core validator. |

### 1.2 JWT security

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-05** | Access tokens shall be JWTs signed with `JWT_SECRET` using `JWT_ALGORITHM` (default HS256), with `exp`, `iat`, `sub`, and `type=access`. | Enforced | Default lifetime **900 seconds** (15 minutes). |
| **NFR-SEC-06** | `JWT_SECRET` and `SECRET_KEY` shall be at least 32 characters. In `ENVIRONMENT=production` they shall not start with `change-me`. | Enforced | Startup validator. |
| **NFR-SEC-07** | The system shall reject tokens that fail signature, expiry, or type checks. | Enforced | `decode_access_token`. |
| **NFR-SEC-08** | Refresh tokens shall be opaque, stored **hashed** (SHA-256), rotated on refresh, and expire after `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default **30 days**). | Enforced | Raw refresh token is not persisted. |

HS256 with a server-side secret is the V1 design. There is no JWKS / RS256 rotation product. Treat secret rotation as an ops procedure outside this repo.

### 1.3 Session security

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-09** | Authenticated API use shall bind to a server-side session identified by `X-Session-ID` when the session was issued. | Enforced | |
| **NFR-SEC-10** | The system shall allow revoke of the current session, other sessions, or all sessions. A revoked session shall not refresh. | Enforced | Logout revokes the session. |
| **NFR-SEC-11** | Email verification OTPs and password-reset tokens shall be stored hashed, with finite TTL (OTP default **15 minutes**, **5** attempts; reset default **1 hour**). | Enforced | |
| **NFR-SEC-12** | After **5** failed logins in **900 seconds**, the account shall lock for **900 seconds**. Lockout counters live in Redis. | Enforced | `ACCOUNT_LOCKOUT_*`. |
| **NFR-SEC-13** | Auth routes shall be rate-limited to `RATE_LIMIT_AUTH` (default **10 requests/minute** per client key). Other API routes shall use `RATE_LIMIT_DEFAULT` (default **100/minute**). Health probes shall be exempt. | Enforced | SlowAPI; storage is Redis. Key is `X-Forwarded-For` first hop or remote address. |

Not in V1: OAuth/OIDC, WebAuthn, MFA beyond email OTP, product API keys.

### 1.4 HTTP hardening

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-14** | Responses shall include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` disabling camera/mic/geolocation, `Cache-Control: no-store`, and a restrictive CSP. Production shall add HSTS (`max-age=31536000; includeSubDomains`). | Enforced | `SecurityHeadersMiddleware`. |
| **NFR-SEC-15** | CORS shall allow only origins in `CORS_ORIGINS`. | Enforced | Credentials allowed when `CORS_ALLOW_CREDENTIALS=true`. CORS is not a substitute for auth. |
| **NFR-SEC-16** | OpenAPI `/docs`, `/redoc`, and `/openapi.json` shall be disabled when `ENVIRONMENT=production`. Public nginx shall not proxy `/metrics`. | Enforced (app + `nginx.prod.conf`) | |
| **NFR-SEC-17** | Agent ingest shall use a per-server credential, not a user JWT. Enrollment tokens (`sbe_…`) shall expire in **15 minutes** and be single-use. Permanent agent tokens shall not be shown in the UI. | Enforced | See FR-MON-*. |

### 1.5 RBAC

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-18** | Every organization-scoped route that mutates or reads tenant data shall go through `require_permission(...)` after an **active** membership is loaded for `X-Organization-ID`. | Enforced | Five roles. Matrix: [RBAC](../security/rbac.md). |
| **NFR-SEC-19** | Missing, inactive, or insufficient membership shall fail closed (401/403), not leak another tenant’s payload. | Enforced | |
| **NFR-SEC-20** | `users.is_superuser` shall not be treated as a product admin path in the UI. | Enforced (by absence) | Column exists; not a documented RBAC role. |

### 1.6 Multi-tenant isolation

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-21** | All tenants shall share one Postgres database. Isolation shall be **logical**: `organization_id` (and `project_id` where relevant) on domain rows, plus membership checks in services. | Enforced | Not separate DBs, not Postgres RLS. |
| **NFR-SEC-22** | Queries for assets, scans, findings, reports, monitoring, audit, and AI conversations shall not return another organization’s rows. Cross-tenant IDs shall 403/404. | Enforced | Regression: `backend/tests/test_org_isolation.py`. |
| **NFR-SEC-23** | There shall be no shared “global assets” across organizations. | Enforced | |

### 1.7 Input validation

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-24** | Request bodies and query parameters shall be validated with Pydantic schemas (types, required fields, `min_length` / `max_length` / enums) before business logic. Invalid input shall return 422, not a 500. | Enforced | |
| **NFR-SEC-25** | Path and body UUIDs shall be parsed as UUIDs. Asset type, scan profile, finding status, and role values shall be restricted to known enums. | Enforced | |
| **NFR-SEC-26** | Nginx shall reject request bodies larger than **20 MB** (`client_max_body_size 20m`). | Enforced | Compose nginx. |
| **NFR-SEC-27** | Scanner plugins shall receive a `ScanTarget`, not a live ORM session, and shall not run caller-supplied shell strings as commands. | Enforced | Plugin authoring rule. Nmap arguments are fixed in the ports plugin when Nmap is present. |

SQL injection is mitigated by SQLAlchemy bound parameters. XSS is mitigated by JSON APIs + CSP + React. These are **controls**, not a pentest attestation.

### 1.8 Secret management

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-28** | Secrets shall be supplied via environment variables / `.env`, not committed. `.env.example` shall contain placeholders only. | Enforced | `SECRET_KEY`, `JWT_SECRET`, DB password, Redis URL, optional OpenAI / Resend / SIEM tokens. |
| **NFR-SEC-29** | Production startup shall refuse default `SECRET_KEY` / `JWT_SECRET` (`change-me…`), a Postgres password containing `changeme`, and a missing `RESEND_API_KEY`. | Enforced | `Settings.validate_production_settings`. |
| **NFR-SEC-30** | Audit logs, AI context, and SIEM payloads shall not include passwords, refresh tokens, OTPs, enrollment tokens, or agent ingest credentials. | Enforced (policy in audit docs) | |
| **NFR-SEC-31** | Compose Grafana default `admin` / `admin` is a **development** credential. Production operators shall override `GRAFANA_ADMIN_*`. | Intent | Not a production control in-repo. |

There is **no** in-repo secret rotation runbook, vault integration, or encrypted backup of `.env`.

### 1.9 Auditability

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SEC-32** | Meaningful domain events shall be written to append-only `audit_logs` with a per-org SHA-256 hash chain. PostgreSQL shall reject UPDATE/DELETE on that table. | Enforced | SQLite tests do **not** have the trigger. Integrity skips unhashed legacy rows. |
| **NFR-SEC-33** | Members with `org:read` shall be able to list, filter, export (CSV/PDF), and integrity-check audit logs. There shall be no public audit endpoint. | Enforced | FR-AUD-*. |
| **NFR-SEC-34** | Application logs shall be structured (`LOG_LEVEL`), include request/correlation IDs, and remain distinct from the compliance audit trail. | Enforced | Loki/Promtail in Compose. |

Hash chain **detects** mutation of hashed rows. It does not stop a DBA from dropping the trigger. Backup/PITR is **not** provided (see Availability).

Scanner trust model: scans run against identifiers the tenant stored on an active asset. There is no IP-ownership proof. Treat `scan:run` as an operator-trust permission ([scanning limits](../security/scanning.md)).

---

## 2. Performance

Targets are for a healthy single-environment stack (Compose or equivalent). There is **no** load-test suite in CI. Do **not** invent figures such as 10k RPS or p99 < 50 ms.

**In scope for the latency target:** login, token refresh, org/project/asset CRUD, membership, finding list/get, dashboard JSON, audit list, report metadata (not PDF generation), monitoring overview reads.

**Out of scope for that target:** scan execution, plugin network I/O, WHOIS, Nmap, PDF render, live OpenAI calls, first request after process start.

| ID | Requirement | Kind | Target |
|----|-------------|------|--------|
| **NFR-PERF-01** | Normal non-scanning API requests shall have **p95 response time < 500 ms**. | Intent | Reasonable for in-process FastAPI + local Postgres. Not asserted in CI. Measure via `/metrics` / Grafana when needed. |
| **NFR-PERF-02** | The API shall accept at most **100 requests/minute** per client key by default, and **10/minute** on auth routes. Excess shall return rate-limit errors, not unbounded work. | Enforced | Ceiling, not a capacity claim. |
| **NFR-PERF-03** | A single HTTP request body shall not exceed **20 MB**. | Enforced | nginx `client_max_body_size`. |
| **NFR-PERF-04** | Each scanner plugin shall honor its timeout (default **30 seconds**; plugins may set higher, e.g. CVE **180 seconds**). A timed-out plugin shall record `timeout` / `scan.plugin_failed` and not block other plugins indefinitely. | Enforced | End-to-end scan time is **unspecified**. |
| **NFR-PERF-05** | Live AI HTTP calls shall timeout after `AI_REQUEST_TIMEOUT_SECONDS` (default **60 seconds**). Output shall be capped at `AI_MAX_OUTPUT_TOKENS` (default **2048**). | Enforced | Temperature default 0.2. |
| **NFR-PERF-06** | In non-development environments, scans and PDF reports shall run **out of the request** (Celery) so the HTTP accept path can still meet NFR-PERF-01. | Enforced | `SCAN_RUN_INLINE` / `REPORT_RUN_INLINE` default false unless development. |
| **NFR-PERF-07** | Agent heartbeats are expected every **30 seconds**. Display delayed at **60 seconds**, offline at **300 seconds**. | Enforced | Monitoring UX, not the p95 target. |
| **NFR-PERF-08** | Throughput (requests/second), concurrent tenants, and scan-queue depth have **no published target**. | Explicitly unspecified | Scale with more API/worker replicas (see Scalability). |

---

## 3. Scalability

V1 is a **modular monolith** with independently scalable process roles. Compose ships **one replica of each** for development. There is no in-repo Kubernetes overlay or multi-region guide ([production](../deployment/production.md)). The table is the scale model; it is not a claim of tested HA.

| Component | Scale model | Role |
|-----------|-------------|------|
| **API** (FastAPI) | **Horizontally scalable** | Stateless request handlers. Access tokens are JWTs (no sticky sessions). Rate limits and lockout use Redis, so multiple API processes share that state. |
| **Celery workers** | **Horizontally scalable** | Compete for jobs on the Redis broker. Add workers to run more scans/reports in parallel. Beat remains a single scheduler. |
| **Plugins** | **Independently extensible** | New scanners implement the plugin interface and register; they do not require a new service or orchestrator. Disabled stubs stay out of the hot path. |
| **PostgreSQL** | **Primary persistence** | System of record for tenants, assets, scans, findings, risk, reports, audit, AI conversations, monitoring. One database, logical tenant isolation. Not scaled by adding a DB per org. |
| **Redis** | **Queue / cache** | Celery broker and result backend, SlowAPI rate-limit storage, login lockout counters. Not the source of truth for tenant data. |

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-SCALE-01** | The API process shall be horizontally scalable: additional replicas behind a load balancer shall not require session affinity. | Intent | JWT access + Redis-backed limiter/lockout. Compose defaults to one API container. |
| **NFR-SCALE-02** | Celery workers shall be horizontally scalable: additional workers shall consume the same Redis queue. | Intent | Scans, reports, schedule checks, agent offline reconcile. |
| **NFR-SCALE-03** | Scanner plugins shall be independently extensible via `ScannerPlugin` / `ScannerPipeline` registration without splitting the monolith. | Enforced | [Plugin authoring](../plugins/authoring.md). |
| **NFR-SCALE-04** | PostgreSQL shall be the primary persistence store. Tenant growth is more rows in one database, not a database per organization. | Enforced | |
| **NFR-SCALE-05** | Redis shall be the queue and cache (broker, rate limits, lockout), not a replica of domain data. | Enforced | `REDIS_URL`. |
| **NFR-SCALE-06** | Multi-region, Postgres read replicas, and automatic tenant sharding are **out of scope**. | Explicitly unspecified | Do not claim active-active HA or 10k-tenant capacity. |

---

## 4. Availability

There is **no** availability percentage in this repository (no 99.9%, no error budget). Expected behavior is **degraded-mode**, not “always up.”

Health:

| Probe | Meaning | When it fails |
|-------|---------|----------------|
| `GET /health` | Process can answer | Only if the API process is down |
| `GET /health/live` | Liveness | Process down |
| `GET /health/ready` | Postgres `SELECT 1` **and** Redis `PING` | **503** if either is disconnected |

Compose backend healthcheck uses `/health/ready`.

### 4.1 Redis unavailable

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-AVL-01** | `/health/ready` shall report Redis `disconnected` and HTTP **503**. Liveness and `/health` shall still succeed if the process is up. | Enforced | |
| **NFR-AVL-02** | Rate limiting and login lockout shall not be trustworthy while Redis is down (both store state in Redis). Operators shall treat auth abuse controls as degraded. | Enforced (consequence) | Do not fail open into “unlimited login” as a *goal* — it is a dependency limitation. |
| **NFR-AVL-03** | Celery shall not consume new scan/report jobs without a broker. In production (non-inline), new scans/reports shall remain queued/pending until Redis and the worker recover. Development inline mode can still run scans in-process. | Enforced | |

### 4.2 Scanner plugin fails

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-AVL-04** | Failure or timeout of one plugin shall be isolated. The scan shall continue other plugins and record `scan.plugin_failed` / plugin run status. The whole scan shall fail only when the orchestrator cannot complete a usable run. | Enforced | FR-SCAN-04. |
| **NFR-AVL-05** | Absence of Nmap shall not fail the ports plugin; it shall run without service detection. | Enforced | FR-PORT-02. |
| **NFR-AVL-06** | Disabled future plugins (`malware`, `cloud`, `kubernetes`) shall not run. A misconfigured optional tool shall not take down the API process. | Enforced | |

### 4.3 AI provider fails or is unset

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-AVL-07** | If `OPENAI_API_KEY` is empty, chat shall return an offline/degraded response and report generation shall use an **offline template** summary. Core assessment (scan, findings, risk, PDF layout) shall still work. | Enforced | |
| **NFR-AVL-08** | If the provider errors or exceeds `AI_REQUEST_TIMEOUT_SECONDS`, the failure shall stay on the AI/report-summary path. It shall not roll back findings or risk scores. | Enforced | Risk is never computed by the model (FR-RSK-06). |

### 4.4 SIEM unavailable

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-AVL-09** | A SIEM sink outage shall **not** fail the user-facing API or the business transaction. Export is best-effort after the audit row is written. | Enforced | Adapters catch and log. |
| **NFR-AVL-10** | With `AUDIT_SIEM_SINK=none` (default), the product shall remain fully usable; audit stays in Postgres. | Enforced | FR-SIEM-03. |

### 4.5 Database temporarily unavailable

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-AVL-11** | `/health/ready` shall report database `disconnected` and HTTP **503**. Orchestrators and UIs that depend on readiness shall stop sending traffic. | Enforced | |
| **NFR-AVL-12** | Tenant reads/writes shall fail (5xx / connection errors) until Postgres returns. The API shall not invent cached tenant data as a substitute source of truth. | Enforced | Redis is not a data replica. |
| **NFR-AVL-13** | A failed audit INSERT shall not fail the business action (SAVEPOINT / fail-safe). A failed **primary** write (asset, scan, finding) shall fail that action — availability of audit is subordinate to correctness of domain data. | Enforced | |

### 4.6 Other availability limits

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-AVL-14** | Automated Postgres backups in production Compose (daily / encrypted / 7-day retention / monthly restore test). No WAL/PITR in-repo. Redis is not durable business data. | Implemented (Compose backup service) | [deployment/backups.md](../deployment/backups.md). |
| **NFR-AVL-15** | Email (Resend) outage shall block production verification/invite/reset delivery. The API may still create hashed tokens; the user cannot complete the email step until mail works. | Intent | Production requires `RESEND_API_KEY` at boot, not a mail SLA. |

---

## 5. Maintainability

### 5.1 Modular services

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-MAINT-01** | Backend features shall live in modules (`auth`, `users`, `organizations`, `members`, `projects`, `assets`, `scans`, `findings`, `risk`, `reports`, `ai`, `audit`, `monitoring`) with their own models, schemas, routers, services, and repositories. | Enforced | Modular monolith, not distributed microservices. |
| **NFR-MAINT-02** | Domain side effects shall publish through `event_bus`. New subscribers (audit, SIEM, later webhooks) shall not require changing publishers. | Enforced | A failing subscriber must not block others. |
| **NFR-MAINT-03** | The frontend shall be a separate React/Vite app talking to `/api/v1`. API contracts shall be versioned under `/api/v1`. | Enforced | |

### 5.2 Plugin interface

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-MAINT-04** | Scanners shall implement `ScannerPlugin` / `ScannerPipeline` (collect → parse → rules), register in the plugin loader, and emit `ScanResult` / findings via the normalizer. | Enforced | [Plugin authoring](../plugins/authoring.md). |
| **NFR-MAINT-05** | Scan profiles shall map to plugin slug lists in one place (`backend/app/scans/profiles.py`). Adding a V1 plugin shall not require a new orchestrator. | Enforced | |
| **NFR-MAINT-06** | Future/stub plugins shall live under `plugins/future/` and default `enabled=False` except the limited CVE lookup. Stubs shall not be documented as shipped product. | Enforced | [Definition](./definition.md). |

### 5.3 Centralized configuration

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-MAINT-07** | Runtime configuration shall be centralized in `backend/app/core/config.py` (Pydantic settings), loaded from the environment. Extra env keys shall be ignored. | Enforced | [environment](../deployment/environment.md), `.env.example`. |
| **NFR-MAINT-08** | Schema changes shall go through Alembic. Operators shall `alembic upgrade head` before relying on new columns (including audit hash chain). | Enforced | Tests often use SQLite `create_all` and **do not** replace a production migrate. |

### 5.4 Automated tests

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-MAINT-09** | Backend changes shall be coverable by `make test` (pytest: `backend/tests/` and `app/*/tests.py`, including plugins and scan engine). Isolation tests shall remain in the suite. | Enforced | |
| **NFR-MAINT-10** | CI/local green `make test` means those suites passed. It does **not** mean frontend e2e, live OpenAI, Postgres trigger immutability, or load tests exist. | Enforced (honesty) | [testing gaps](../testing/gaps.md). There is **no** frontend Jest/Vitest script in V1. |
| **NFR-MAINT-11** | New V1 behavior should add or extend pytest coverage in the matching module rather than relying only on manual clicks. | Intent | Especially auth, isolation, RBAC, risk math, audit integrity. |

### 5.5 Documentation

| ID | Requirement | Kind | Notes |
|----|-------------|------|-------|
| **NFR-MAINT-12** | Product source of truth shall be `docs/product/`. Architecture, database, security, testing, deployment, and roadmap folders shall describe **current code**, not a wishlist. | Enforced | [docs/README](../README.md). |
| **NFR-MAINT-13** | If a feature README disagrees with `docs/product/`, `docs/product/` wins until the deep-dive is updated. | Enforced | |
| **NFR-MAINT-14** | Stubs, disabled plugins, and missing SLAs shall be named in product/roadmap docs so maintainers do not “complete” them by accident. | Enforced | |

---

## Requirement count

| Area | IDs | Count |
|------|-----|------:|
| Security (hashing, JWT, session, HTTP, RBAC, tenancy, validation, secrets, audit) | NFR-SEC-01 … 34 | 34 |
| Performance | NFR-PERF-01 … 08 | 8 |
| Scalability | NFR-SCALE-01 … 06 | 6 |
| Availability | NFR-AVL-01 … 15 | 15 |
| Maintainability | NFR-MAINT-01 … 14 | 14 |
| **Total** | | **77** |

**Traceability:** [requirements/traceability-matrix.md](../requirements/traceability-matrix.md).

---

## What this document does not claim

| Claim | Reality |
|-------|---------|
| 99.9% uptime | Not specified; no HA topology in-repo |
| p99 / RPS SLA | Not measured |
| Per-tenant Postgres or RLS | Logical `organization_id` only |
| Secret vault / key rotation product | Env vars + production startup checks |
| Automated backups | Production Compose `backup` service — [deployment/backups.md](../deployment/backups.md) |
| Frontend test gate | Typecheck/build only |
| Scanner legal authorization | Operator-trust model |

Deep-dives: [security known limits](../security/known-limits.md), [roadmap limitations](../roadmap/known-limitations.md), [production constraints](../deployment/production.md).
