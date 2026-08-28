# Configuration

All runtime settings are loaded from the environment into `backend/app/core/config.py` (Pydantic `Settings`). Compose services read `.env` via `env_file` and apply additional overrides in `docker-compose.yml`.

Extra keys in `.env` are **ignored** — only declared fields are used.

Reference template: `.env.example` at the repository root.

## Required variables

These must be set for any environment:

| Variable | Purpose |
|----------|---------|
| `POSTGRES_HOST` | Database host (`postgres` in Compose; `localhost` if backend runs on host) |
| `POSTGRES_PORT` | Default `5432` |
| `POSTGRES_DB` | Database name (default `sandbox`) |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `SECRET_KEY` | App secret; **minimum 32 characters** |
| `JWT_SECRET` | JWT signing key; **minimum 32 characters** |
| `REDIS_URL` | Celery broker and Redis client (Compose: `redis://redis:6379/0`) |

Validation runs at import time. Invalid secrets raise a startup error before the API accepts traffic.

## Environment mode

| Variable | Values | Default |
|----------|--------|---------|
| `ENVIRONMENT` | `development`, `staging`, `production` | `development` |

Effects:

| Setting | Development (default) | Production |
|---------|----------------------|------------|
| OpenAPI `/docs`, `/redoc`, `/openapi.json` | Enabled | **Disabled** (app + nginx) |
| Prometheus `/metrics` on public edge | Proxied (dev nginx) | **404** at nginx; scrape `backend:8000/metrics` internally |
| `SCAN_RUN_INLINE` | `true` (unless set) | `false` |
| `REPORT_RUN_INLINE` | `true` (unless set) | `false` |
| Production validator | Skipped | Enforces non-default secrets, password, Resend |

See [production.md](./production.md) for production-specific requirements.

## Security and HTTP

| Variable | Default | Purpose |
|----------|---------|---------|
| `CORS_ORIGINS` | localhost Vite + :80 | Comma-separated allowed origins |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow cookies/credentials in CORS |
| `RATE_LIMIT_DEFAULT` | `100/minute` | General API rate limit |
| `RATE_LIMIT_AUTH` | `10/minute` | Auth endpoint rate limit |

Health routes (`/health`, `/health/live`, `/health/ready`) are exempt from rate limiting.

## JWT and sessions

| Variable | Default |
|----------|---------|
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_SECONDS` | `900` (15 min) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` |
| `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` | `1` |
| `EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES` | `15` |
| `EMAIL_VERIFICATION_OTP_MAX_ATTEMPTS` | `5` |
| `ORGANIZATION_INVITE_EXPIRE_DAYS` | `7` |

## Account lockout

| Variable | Default | Meaning |
|----------|---------|---------|
| `ACCOUNT_LOCKOUT_MAX_ATTEMPTS` | `5` | Failed logins before lock |
| `ACCOUNT_LOCKOUT_WINDOW_SECONDS` | `900` | Window for counting failures |
| `ACCOUNT_LOCKOUT_DURATION_SECONDS` | `900` | Lock duration |

## URLs used in emails and agents

| Variable | Default | Purpose |
|----------|---------|---------|
| `FRONTEND_URL` | `http://localhost` | Links in password reset and verification emails |
| `PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Shown in monitoring agent install commands |
| `AGENT_ENROLLMENT_TOKEN_EXPIRE_MINUTES` | `15` | One-time enrollment token lifetime |

When nginx is the public entry, set `FRONTEND_URL` to your public origin (e.g. `https://app.example.com`). Set `PUBLIC_API_URL` to the URL agents can reach (often the same host with `/api/v1`).

## Background work mode

| Variable | Default when unset | Purpose |
|----------|-------------------|---------|
| `SCAN_RUN_INLINE` | `true` in development | Run scan orchestrator in API process |
| `REPORT_RUN_INLINE` | `true` in development | Run PDF generation in API process |

When `false`, Celery worker must be running or scans/reports stay queued.

## Report file storage

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPORT_STORAGE_BACKEND` | `local` | `local` (mounted volume) or `s3` |
| `REPORT_STORAGE_PATH` | `/app/storage/reports` | Directory for local backend |
| `REPORT_S3_BUCKET` | empty | Required when backend is `s3` |
| `REPORT_S3_PREFIX` | empty | Optional key prefix |
| `REPORT_S3_REGION` | `us-east-1` | AWS region |
| `REPORT_S3_ENDPOINT_URL` | empty | MinIO / custom S3 endpoint |
| `REPORT_S3_ACCESS_KEY_ID` | empty | Optional if using IAM role |
| `REPORT_S3_SECRET_ACCESS_KEY` | empty | Optional if using IAM role |

Details: [reports/storage.md](../reports/storage.md).

## Automated backups (production Compose)

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKUP_ENCRYPTION_PASSPHRASE` | empty | **Required in production** — AES-256 via openssl |
| `BACKUP_RETENTION_DAYS` | `7` | Delete artifacts older than N days |
| `BACKUP_REPORT_FILES` | `true` | Include report volume in daily backup |
| `BACKUP_S3_URI` | empty | Optional offsite `s3://bucket/prefix` |

Service: `docker-compose.prod.yml` → `backup`. Details: [backups.md](./backups.md).

## Email (Resend)

| Variable | Default | Notes |
|----------|---------|-------|
| `RESEND_API_KEY` | empty | **Required** when `ENVIRONMENT=production` |
| `RESEND_FROM` | `Sandbox <onboarding@resend.dev>` | Sender address |

Without `RESEND_API_KEY` in development, registration still works if users are marked verified manually or via seed script; production startup **fails** without it.

## AI assistant

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | empty | Live model calls; empty = offline templates |
| `AI_MODEL` | `gpt-4o-mini` | Chat and report summary model |
| `AI_TEMPERATURE` | `0.2` | |
| `AI_MAX_OUTPUT_TOKENS` | `2048` | |
| `AI_REQUEST_TIMEOUT_SECONDS` | `60` | |

## Audit SIEM export

| Variable | Default | Purpose |
|----------|---------|---------|
| `AUDIT_SIEM_SINK` | `none` | `none`, `syslog`, `splunk`, `elk`, `sentinel` |

Sink-specific variables (only used when sink matches):

- **Syslog:** `AUDIT_SYSLOG_HOST`, `AUDIT_SYSLOG_PORT`, `AUDIT_SYSLOG_PROTOCOL`
- **Splunk HEC:** `AUDIT_SPLUNK_HEC_URL`, `AUDIT_SPLUNK_HEC_TOKEN`
- **ELK:** `AUDIT_ELK_URL`, `AUDIT_ELK_INDEX`, `AUDIT_ELK_API_KEY`
- **Azure Sentinel:** `AUDIT_SENTINEL_WORKSPACE_ID`, `AUDIT_SENTINEL_SHARED_KEY`, `AUDIT_SENTINEL_LOG_TYPE`

SIEM export is best-effort; API requests succeed even if the sink is down.

## Compose-only variables

These appear in `.env.example` for Compose port mapping and Grafana bootstrap — they are **not** read by `config.py`:

| Variable | Default | Used by |
|----------|---------|---------|
| `NGINX_PORT` | `80` | `docker-compose.yml` nginx ports |
| `GRAFANA_PORT` | `3000` | Grafana host port |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana initial admin |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana initial admin |

Change Grafana credentials before any shared or production deployment.

## Frontend container

The dev frontend service sets:

```
VITE_API_BASE_URL=/api/v1
```

So the browser talks to the API through nginx on the same origin. For standalone Vite (`npm run dev` on the host), point `VITE_API_BASE_URL` at your API and ensure `CORS_ORIGINS` includes `http://localhost:5173`.

## Logging

| Variable | Default |
|----------|---------|
| `LOG_LEVEL` | `INFO` |

Structured JSON logs from the backend; Promtail ships container logs to Loki when the monitoring stack is up.

## Configuration checklist

**Local development**

- [ ] `.env` copied from `.env.example`
- [ ] `SECRET_KEY` and `JWT_SECRET` ≥ 32 characters
- [ ] `make migrate` applied
- [ ] Optional: `RESEND_API_KEY` for real email OTP

**Production**

- [ ] `ENVIRONMENT=production`
- [ ] Non-default `SECRET_KEY`, `JWT_SECRET`, `POSTGRES_PASSWORD`
- [ ] `RESEND_API_KEY` set
- [ ] `FRONTEND_URL` and `PUBLIC_API_URL` match public URLs
- [ ] `CORS_ORIGINS` lists only trusted origins
- [ ] Grafana admin password changed
- [ ] TLS terminated in front of nginx (not in-repo)
- [ ] Celery worker + beat running (`SCAN_RUN_INLINE=false`)

Related: [environment.md](./environment.md) (legacy quick reference), [health.md](./health.md) (probes).
