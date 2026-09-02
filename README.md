# Sandbox

**Security Intelligence Platform** — multi-tenant workspace to inventory assets you operate, run plugin-based scans, triage findings, score risk deterministically, explain results with AI, publish PDF reports, monitor enrolled servers, and keep an auditable activity trail.

This README is the front door. Detailed truth lives under [`docs/`](docs/README.md).

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

Modular monolith: one FastAPI app, PostgreSQL, Redis, Celery, React SPA, nginx edge.

```
Browser
   │
   ▼
Nginx (:80)
   ├─ /        → Frontend (Vite / React)
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

Full diagrams: [docs/architecture/system.md](docs/architecture/system.md).  
Why these choices: [docs/architecture/decisions/](docs/architecture/decisions/README.md).

---

## Features

- Multi-tenant orgs with five roles: `owner`, `admin`, `security_analyst`, `manager`, `viewer`
- JWT access + refresh, sessions (`X-Session-ID`), email OTP, lockout
- Asset ownership verification (domain, DNS TXT, HTTP, IP) — mandatory for website/domain/public_ip before scan
- Plugin scan engine with isolated plugin failures
- Scheduled scans (Celery beat)
- Security Intelligence dashboard with selectable history ranges (7d / 30d / 90d / 1y)
- Hash-chained audit logs + integrity API
- Compose stack with Prometheus, Grafana, Loki

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Jobs | Celery, Redis |
| DB | PostgreSQL 16 |
| Frontend | React 19, TypeScript, Vite, Tailwind, TanStack Query |
| Edge | nginx |
| Observability | Prometheus, Grafana, Loki, Promtail |
| Agent | Python monitoring agent (read-only) |
| Runtime | Docker Compose |

---

## Screenshots

UI product screenshots are not checked into the repo yet. Auth and token flow diagrams:

| Flow | Diagram |
|------|---------|
| Login | ![Login flow](docs/diagrams/login%20flow.png) |
| Register | ![Register flow](docs/diagrams/register%20flow.png) |
| Token lifecycle | ![Token lifecycle](docs/diagrams/token%20lifecycle.png) |
| Enforcement | ![Enforcement](docs/diagrams/enforcement%20mechanism.png) |

After seeding demo data, open http://localhost for the live UI. Contributions welcome under `docs/screenshots/`.

---

## Quick start

**Prerequisites:** Docker Compose v2, free ports (80, 5432, 6379, 3000, …).

```bash
git clone <repository-url> sandbox
cd sandbox
cp .env.example .env          # keep SECRET_KEY / JWT_SECRET ≥ 32 chars
docker compose up -d          # or: make up
make migrate                  # required — schema is not applied automatically
make seed                     # optional demo tenant
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

Copy [`.env.example`](.env.example) → `.env`. Required always:

| Variable | Purpose |
|----------|---------|
| `POSTGRES_*` | Database connection |
| `SECRET_KEY` | App secret (≥ 32 chars) |
| `JWT_SECRET` | JWT signing (≥ 32 chars) |
| `REDIS_URL` | Celery + rate limits + lockout |

Notable optionals:

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `development` \| `staging` \| `production` |
| `OPENAI_API_KEY` | Live AI; empty = offline / degraded |
| `RESEND_API_KEY` | Email; **required** when `ENVIRONMENT=production` |
| `AUDIT_SIEM_SINK` | `none` \| `syslog` \| `splunk` \| `elk` \| `sentinel` |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `FRONTEND_URL` / `PUBLIC_API_URL` | Links in email and agent install |

Compose overrides `POSTGRES_HOST=postgres` and Redis URL inside containers.

Full reference: [docs/deployment/configuration.md](docs/deployment/configuration.md).

---

## Running tests

```bash
make test
# equivalent:
# cd backend && pip install -r requirements-dev.txt && python -m pytest tests app -q
```

Covers backend integration and unit tests (auth, RBAC, isolation, scans, audit, dashboard, …).  
There is **no** frontend Jest/Vitest suite in V1 (`npm run typecheck` / `npm run build` only).

**CI:** every push/PR runs pytest, frontend build, production Docker build, secret checks, staging acceptance, and a database restore drill — [docs/deployment/ci.md](docs/deployment/ci.md). Local fast gate: `make ci`. Full local gate: `make ci-full`.

Strategy and gaps: [docs/testing/](docs/testing/README.md).

---

## Deployment

| Doc | Use |
|-----|-----|
| [Installation](docs/deployment/installation.md) | Clone → `.env` → Compose → migrate |
| [Production](docs/deployment/production.md) | Validator gates and hardening |
| [CI quality gate](docs/deployment/ci.md) | GitHub Actions — pytest, build, secrets, staging e2e, restore drill |
| [Production runbook](docs/deployment/production-runbook.md) | Startup, health, logs, restart, incidents |
| [Backups](docs/deployment/backups.md) | Daily Postgres / retention / restore; Redis is ephemeral |
| [Troubleshooting](docs/deployment/troubleshooting.md) | Common failures |

Production requires non-default secrets, a real `POSTGRES_PASSWORD`, and `RESEND_API_KEY`. Compose as shipped is a **dev stack** (reload, bind mounts, default Grafana).

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
├── infrastructure/     # nginx, Prometheus, Grafana, Loki configs
├── scanner-sdk/        # Shared scanner contracts / SDK
├── scripts/            # Utility scripts
├── shared/             # Shared packages (if any)
├── docker-compose.yml
├── Makefile
└── .env.example
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

Full list: **[docs/known-limitations.md](docs/known-limitations.md)**.

---

## Makefile cheatsheet

| Command | Action |
|---------|--------|
| `make up` | `docker compose up -d` |
| `make down` | Stop containers (volumes kept) |
| `make migrate` | `alembic upgrade head` |
| `make seed` | Demo tenant |
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
