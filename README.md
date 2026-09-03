# Sandbox

**Security Intelligence Platform** — multi-tenant workspace to inventory assets you operate, run plugin-based scans, triage findings, score risk deterministically, explain results with AI, publish PDF reports, monitor enrolled servers, and keep an auditable activity trail.

This README is the front door. Detailed truth lives under [`docs/`](docs/README.md).

V1 is a **single-node Docker Compose** application behind a **Caddy HTTPS** edge. Production readiness is validated through automated tests, staging end-to-end testing, security checks, persistence testing (durable PDF after restart), and a database restore drill. The platform does **not** provide HA, autoscaling, multi-region deployment, enterprise SLA guarantees, or a dedicated WAF / secrets-management product.

---

## What is this?

Sandbox helps organizations that **already manage** their infrastructure close the gap between scattered tools and a single security posture product.

It is **not** a general-purpose attack platform. Scanning is authorized against org/project assets (with ownership verification for `website`, `domain`, and `public_ip`). See [Security model](#security-model) and [Known limitations](#known-limitations).

## What does it do?

| Capability | Behavior |
|------------|----------|
| **Assets** | Inventory websites, domains, IPs, servers, and related types with hierarchy, tags, and projects |
| **Scans** | Quick / full / custom profiles via plugins (HTTP headers, TLS, DNS, WHOIS, ports, cookies, robots, security.txt, fingerprint, CVE hints) |
| **Findings** | Normalized severity, status, evidence, and review workflow |
| **Risk** | Deterministic scores and letter grades (A+–F) — AI does not invent the score |
| **Dashboard** | Org posture, risk trend, scan history, finding trends, risky assets, upcoming scans |
| **Reports** | Executive / technical / weekly / monthly PDFs |
| **AI** | Org-scoped chat over structured facts when `OPENAI_API_KEY` is set |
| **Monitoring** | Read-only agent on enrolled `server` / `windows_server` / `docker_host` assets |
| **Audit** | Append-only logs, per-org hash chain, optional SIEM export |

---

## Architecture

V1 production is a **single-node Docker Compose** app. Public HTTPS is **Caddy** (`docker-compose.edge.yml`) in front of app nginx. There is no HA, autoscaling, multi-region, enterprise SLA, WAF, or in-repo secrets vault.

```
User
 │  HTTPS :443
 ▼
Caddy (TLS, Let's Encrypt)
 │  HTTP (internal)
 ▼
Nginx
 ├─ /        → Frontend (React static)
 └─ /api/*   → Backend (FastAPI :8000)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   PostgreSQL     Redis     Celery worker + beat
                    │
              Scan / report jobs
                    │
              Plugin pipeline → findings → risk → audit bus
```

Local development skips Caddy and uses nginx on `:80` (`docker-compose.yml`). Postgres/Redis stay on the host for debugging.

Full diagrams: [docs/architecture/system.md](docs/architecture/system.md).  
Why these choices: [docs/architecture/decisions/](docs/architecture/decisions/README.md).  
Production HTTPS: [docs/deployment/tls-edge.md](docs/deployment/tls-edge.md).

---

## Features

- Multi-tenant orgs with five roles: `owner`, `admin`, `security_analyst`, `manager`, `viewer`
- JWT access + refresh, sessions (`X-Session-ID`), email OTP, lockout
- Asset ownership verification (domain, DNS TXT, HTTP, IP) — mandatory for website/domain/public_ip before scan
- Plugin scan engine with isolated plugin failures
- Scheduled scans (Celery beat)
- Security Intelligence dashboard with selectable history ranges (7d / 30d / 90d / 1y)
- Hash-chained audit logs + integrity API
- Dev Compose stack with Prometheus, Grafana, Loki (not in the production compose file)

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Jobs | Celery, Redis |
| DB | PostgreSQL 16 |
| Frontend | React 19, TypeScript, Vite, Tailwind, TanStack Query |
| Edge | nginx (app); Caddy (production TLS) |
| Observability | Prometheus, Grafana, Loki, Promtail (dev Compose only) |
| Agent | Python monitoring agent (read-only) |
| Runtime | Docker Compose (one replica of each service) |

---

## Screenshots

UI product screenshots are not checked into the repo yet. Auth and token flow diagrams:

| Flow | Diagram |
|------|---------|
| Login | ![Login flow](docs/diagrams/login%20flow.png) |
| Register | ![Register flow](docs/diagrams/register%20flow.png) |
| Token lifecycle | ![Token lifecycle](docs/diagrams/token%20lifecycle.png) |
| Enforcement | ![Enforcement](docs/diagrams/enforcement%20mechanism.png) |

After seeding **demo** data on the local stack, open http://localhost for the live UI. Contributions welcome under `docs/screenshots/`.

---

## Quick start (local / demo)

This is the **dev** stack (`sandbox-dev`). It is not production. `make seed` is optional and **must not** run on the prod stack.

**Prerequisites:** Docker Compose v2, free ports (80, 5432, 6379, 3000, …).

```bash
git clone <repository-url> sandbox
cd sandbox
cp .env.example .env          # keep SECRET_KEY / JWT_SECRET ≥ 32 chars
docker compose up -d          # or: make up
make migrate                  # required — schema is not applied automatically
make seed                     # optional Demo Corp tenant
```

| What | URL / value |
|------|-------------|
| App | http://localhost |
| OpenAPI (non-production) | http://localhost/docs |
| Grafana | http://localhost:3000 (`admin` / `admin` by default) |
| Demo owner | `owner@demo.sandbox` / `DemoPassword1!` |

Org-scoped API calls need:

```http
Authorization: Bearer <access_token>
X-Organization-ID: <uuid>
```

Full boot sequence: [docs/deployment/installation.md](docs/deployment/installation.md).

---

## Environment variables

| Stack | Template | Compose |
|-------|----------|---------|
| Local / demo | [`.env.example`](.env.example) | `docker-compose.yml` |
| Staging | [`.env.staging.example`](.env.staging.example) | `docker-compose.prod.yml` + `docker-compose.staging.yml` |
| Production | [`.env.production.example`](.env.production.example) | `docker-compose.prod.yml` + `docker-compose.edge.yml` |

Copy the matching template → `.env`. Do not commit `.env`. Demo and production use **separate Compose projects and volumes** (`sandbox-dev` vs `sandbox-prod`); the database name is `sandbox` in both.

Required always:

| Variable | Purpose |
|----------|---------|
| `POSTGRES_*` | Database connection |
| `SECRET_KEY` | App secret (≥ 32 chars) |
| `JWT_SECRET` | JWT signing (≥ 32 chars) |
| `REDIS_URL` | Celery + rate limits + lockout |

Production also requires (startup fails otherwise):

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT=production` | Enables the production validator |
| `RESEND_API_KEY` | Transactional email |
| `BACKUP_ENCRYPTION_PASSPHRASE` | Encrypted Postgres backups |
| `FRONTEND_URL` / `PUBLIC_API_URL` / `CORS_ORIGINS` | Public **HTTPS** origins (not localhost) |
| `EDGE_DOMAIN` / `ACME_EMAIL` | Caddy site + Let's Encrypt |

Notable optionals:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Live AI; empty = offline / degraded. Production needs this if `AI_ENABLED=true` |
| `AUDIT_SIEM_SINK` | `none` \| `syslog` \| `splunk` \| `elk` \| `sentinel` |

Compose overrides `POSTGRES_HOST=postgres` and Redis URL inside containers.

Full reference: [docs/deployment/configuration.md](docs/deployment/configuration.md).

---

## Running tests

```bash
make test
# equivalent:
# cd backend && pip install -r requirements-dev.txt && python -m pytest tests app -q -m "not docker"
```

Covers backend integration and unit tests (auth, RBAC, isolation, scans, audit, dashboard, …).  
There is **no** frontend Jest/Vitest suite in V1 (`npm run typecheck` / `npm run build` only).

**CI quality gate** (every push/PR): pytest, frontend build, production Docker build, Caddy validate, secret checks, **staging end-to-end**, and a **database restore drill**. That is the automated proof for production readiness — [docs/deployment/ci.md](docs/deployment/ci.md).

Local: `make ci` (fast). Full gate: `make ci-full`.

Strategy and gaps: [docs/testing/](docs/testing/README.md).

---

## Deployment

**Local / demo** uses `docker-compose.yml` + `.env.example` + optional `make seed` (`demo-corp`, `owner@demo.sandbox`).  
**Production** is a different stack and volume. Never seed it.

```bash
cp .env.production.example .env
# replace every CHANGE-ME / example.com; set EDGE_DOMAIN, ACME_EMAIL, HTTPS URLs, Resend, backup passphrase
# DNS for EDGE_DOMAIN must already point at this host
make prod-edge-migrate
make prod-edge-up
```

Traffic: `Internet → HTTPS :443 → Caddy → nginx → frontend + /api`. Firewall: 80 and 443 only.

The platform does **not** provide HA, autoscaling, multi-region, an enterprise SLA, a WAF, or a dedicated secrets-management product. Secrets live in `.env` (operator vault is outside this repo).

| Doc | Use |
|-----|-----|
| [Installation](docs/deployment/installation.md) | Local clone → `.env` → Compose → migrate |
| [TLS edge](docs/deployment/tls-edge.md) | Caddy HTTPS, Let's Encrypt, bring-your-own proxy |
| [Production](docs/deployment/production.md) | Validator gates and hardening |
| [CI quality gate](docs/deployment/ci.md) | GitHub Actions — tests, secrets, staging e2e, restore drill |
| [Production runbook](docs/deployment/production-runbook.md) | Startup, health, logs, restart, incidents |
| [Backups](docs/deployment/backups.md) | Daily Postgres / retention / restore; Redis is ephemeral |
| [Troubleshooting](docs/deployment/troubleshooting.md) | Common failures |

---

## Security model

1. Authenticated user + org membership (`X-Organization-ID`)
2. RBAC permissions (`scan:run`, `asset:update`, …)
3. Asset must belong to the org/project and be `active`
4. For `website` / `domain` / `public_ip`: ownership verification must be `verified`
5. Then scan orchestration runs

Additional controls: hashed passwords (Argon2), short-lived JWT + refresh rotation, session binding, rate limits, account lockout, append-only audit with per-org hash chain, optional SIEM export.

Details: [docs/security/](docs/security/README.md), [docs/security/scanning.md](docs/security/scanning.md).

---

## Project structure

```
sandbox/
├── agent/              # Read-only monitoring agent
├── backend/            # FastAPI app, Alembic, Celery, plugins, tests
├── frontend/           # React + Vite SPA
├── docs/               # Product, architecture, security, deployment (source of truth)
├── infrastructure/     # nginx, Caddy, backup, Prometheus/Grafana/Loki (dev)
├── scanner-sdk/        # Shared scanner contracts / SDK
├── scripts/            # Utility scripts
├── shared/             # Shared packages (if any)
├── docker-compose.yml              # local / demo (sandbox-dev)
├── docker-compose.prod.yml         # production data plane (sandbox-prod)
├── docker-compose.edge.yml         # Caddy HTTPS overlay
├── Makefile
├── .env.example
├── .env.staging.example
└── .env.production.example
```

---

## Documentation

| Area | Start here |
|------|------------|
| Index | [docs/README.md](docs/README.md) |
| Glossary / naming | [docs/glossary.md](docs/glossary.md) |
| Requirements traceability | [docs/requirements/traceability-matrix.md](docs/requirements/traceability-matrix.md) |
| Product / FR / NFR | [docs/product/](docs/product/README.md) |
| Architecture | [docs/architecture/](docs/architecture/README.md) |
| ADRs | [docs/architecture/decisions/](docs/architecture/decisions/README.md) |
| Database | [docs/database/](docs/database/README.md) |
| Security | [docs/security/](docs/security/README.md) |
| Testing | [docs/testing/](docs/testing/README.md) |
| Deployment | [docs/deployment/](docs/deployment/README.md) |
| Demo data | [docs/demo-data.md](docs/demo-data.md) |

---

## Roadmap

Later work (not shipped): API keys, webhooks, notification delivery, org restore, billing UI, stronger cloud/K8s scanners, production K8s overlay, frontend e2e.

See [docs/roadmap/planned.md](docs/roadmap/planned.md).

---

## Known limitations

A serious project states its boundaries. Highlights:

- Nmap `-sV` is optional
- No CIDR/ASN ownership allowlist
- Webhooks and analytics consumers are not implemented
- AI depends on provider availability
- Legacy audit rows may lack hash-chain values
- Dashboard trend charts are simplified
- Automated Postgres backups in production Compose ([backups](docs/deployment/backups.md))
- Redis is ephemeral — not business data
- Single-node Compose only — no HA, autoscaling, multi-region, published SLA, WAF, or vault product

Full list: **[docs/known-limitations.md](docs/known-limitations.md)**.

---

## Makefile cheatsheet

| Command | Action |
|---------|--------|
| `make up` | `docker compose up -d` |
| `make down` | Stop containers (volumes kept) |
| `make migrate` | `alembic upgrade head` |
| `make seed` | Demo tenant (dev stack only — never on prod) |
| `make prod-edge-migrate` | Alembic on prod + Caddy compose |
| `make prod-edge-up` | Production stack behind Caddy |
| `make logs` | Follow all logs |
| `make backend-logs` | API + Celery |
| `make test` | Backend pytest |
| `make ci` | Fast CI locally (tests + frontend build + prod Docker + secret checks) |
| `make ci-full` | GitHub quality gate locally (`make ci` + restore drill + staging e2e) |
| `make staging-acceptance` | Staging Compose e2e (workers, PDF after restart) |
| `make backup-integration-test` | Encrypted backup → restore drill |
| `make shell` | Bash in backend container |

---

## Contributing / docs honesty

If code and docs disagree, **`docs/product/` and the seven folders listed in [docs/README.md](docs/README.md) win** until the deep-dive is updated. Do not document wishlist items as shipped.
