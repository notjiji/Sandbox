# Staging deployment

Staging sits between **CI** and **production**. It runs the same Compose topology as production (workers, durable report storage, internal Postgres/Redis) but with `ENVIRONMENT=staging` so the production validator is skipped and OpenAPI remains available for debugging.

```
Local (development Compose)
        ↓
CI (pytest + build + secret checks)
        ↓
Staging (prod Compose + staging overlay)  ← you are here
        ↓
Full workflow acceptance test
        ↓
Production (prod Compose + TLS edge)
```

---

## Quick start

```bash
cp .env.staging.example .env
# edit passwords and URLs if needed

make staging-migrate
make staging-up
```

Open http://localhost (default `NGINX_HTTP_PORT=80`).

---

## What staging proves

| Area | Staging behaviour |
|------|-------------------|
| Background jobs | `SCAN_RUN_INLINE=false`, `REPORT_RUN_INLINE=false` — Celery worker required |
| Report storage | PDF bytes on `report_storage` volume (same as production) |
| Workers | Healthchecks + restart policy from [workers.md](./workers.md) |
| Config | No production HTTPS validator; HTTP localhost URLs OK |
| OpenAPI | `/docs` enabled (staging only) |
| Email OTP | `STAGING_FIXED_OTP=123456` for repeatable acceptance |

---

## Acceptance test (full product story)

The acceptance test is the **actual product narrative**, including previous weak points:

1. Register → Login  
2. Create organization → project → asset  
3. Ownership challenge → verify asset (HTTP token on `mock-target`)  
4. Launch authorized scan → **Celery worker executes plugins**  
5. Findings normalized → risk calculated → **dashboard updated**  
6. Generate PDF via worker → download  
7. **Restart `backend` + `celery-worker`** → re-download PDF (durable storage)  
8. Review audit trail + integrity + CSV export  

Run:

```bash
make staging-acceptance
```

Or:

```bash
bash scripts/staging/run-acceptance.sh
```

Requires Docker. Creates `.env.staging.acceptance` from `.env.staging.example` on first run. Test module: `backend/tests/test_staging_acceptance.py`.

Optional env overrides:

| Variable | Default |
|----------|---------|
| `STAGING_HTTP_PORT` | `18080` (acceptance test; avoids clashing with other stacks on `:80`) |
| `STAGING_BASE_URL` | derived from `STAGING_HTTP_PORT` in the acceptance test |
| `STAGING_MOCK_TARGET_URL` | `http://mock-target.test` (Docker alias on `internal` network) |
| `STAGING_FIXED_OTP` | `123456` |
| `STAGING_POLL_TIMEOUT` | `180` (seconds) |

---

## Compose files

| File | Role |
|------|------|
| `docker-compose.prod.yml` | Base production topology |
| `docker-compose.staging.yml` | Staging env, mock scan target, env file overrides |

Services added in staging:

| Service | Role |
|---------|------|
| `mock-target` | HTTP target for ownership verification + scan plugins |

---

## Environment template

Copy `.env.staging.example` → `.env` (or `.env.staging.acceptance` for acceptance only).

Key variables:

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT=staging` | Staging mode |
| `STAGING_FIXED_OTP` | Fixed email verification code for acceptance |
| `SCAN_RUN_INLINE=false` | Queue scans to Celery |
| `REPORT_RUN_INLINE=false` | Queue PDF generation to Celery |
| `REPORT_STORAGE_BACKEND=local` | Durable PDF volume |

Full list: [configuration.md](./configuration.md).

---

## Staging vs production

| | Staging | Production |
|---|---------|------------|
| Validator | Skipped | Strict HTTPS, secrets, email, backups |
| TLS edge | Optional HTTP on `:80` | Caddy overlay or external proxy |
| OpenAPI | Enabled | Disabled |
| AI | `AI_ENABLED=false` default in example | Explicit policy |
| Backups | Optional | Required encrypted passphrase |

Promote to production: [production.md](./production.md), [tls-edge.md](./tls-edge.md).

---

## CI integration

Pre-merge **CI** runs fast pytest (SQLite, inline jobs) — see [ci.md](./ci.md).

Run staging acceptance **manually** before production cutover:

```bash
make staging-acceptance
```

Optional GitHub Actions workflow: `.github/workflows/staging-acceptance.yml` (`workflow_dispatch`).

Related: [production-runbook.md](./production-runbook.md), [testing/gaps.md](../testing/gaps.md).
