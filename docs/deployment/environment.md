# Environment variables

Defined in `backend/app/core/config.py`. Extra keys ignored. Example: `.env.example`.

## Required always

`POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `SECRET_KEY`, `JWT_SECRET`, `REDIS_URL`.

Secrets must be at least 32 characters.

## Common

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_PORT` | 5432 | DB port |
| `ENVIRONMENT` | development | development / staging / production |
| `LOG_LEVEL` | INFO | |
| `CORS_ORIGINS` | localhost Vite + :80 | Comma-separated |
| `CORS_ALLOW_CREDENTIALS` | true | |
| `RATE_LIMIT_DEFAULT` | 100/minute | |
| `RATE_LIMIT_AUTH` | 10/minute | |
| `JWT_ALGORITHM` | HS256 | |
| `JWT_ACCESS_TOKEN_EXPIRE_SECONDS` | 900 | |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 30 | |
| `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` | 1 | |
| `ORGANIZATION_INVITE_EXPIRE_DAYS` | 7 | |
| `EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES` | 15 | |
| `EMAIL_VERIFICATION_OTP_MAX_ATTEMPTS` | 5 | |
| `ACCOUNT_LOCKOUT_*` | 5 / 900 / 900 | Attempts, window, duration |
| `FRONTEND_URL` | http://localhost | Links in emails |
| `PUBLIC_API_URL` | http://localhost:8000/api/v1 | Agent install commands |
| `AGENT_ENROLLMENT_TOKEN_EXPIRE_MINUTES` | 15 | |
| `SCAN_RUN_INLINE` | unset → true iff development | |
| `REPORT_RUN_INLINE` | unset → true iff development | |
| `OPENAI_API_KEY` | empty | Live AI |
| `AI_MODEL` | gpt-4o-mini | |
| `AI_TEMPERATURE` | 0.2 | |
| `AI_MAX_OUTPUT_TOKENS` | 2048 | |
| `AI_REQUEST_TIMEOUT_SECONDS` | 60 | |
| `RESEND_API_KEY` | empty | Required in production |
| `RESEND_FROM` | Sandbox onboarding@resend.dev | |
| `AUDIT_SIEM_SINK` | none | none / syslog / splunk / elk / sentinel |
| `AUDIT_SYSLOG_*` / `AUDIT_SPLUNK_*` / `AUDIT_ELK_*` / `AUDIT_SENTINEL_*` | empty | Used only if sink matches |
| `NGINX_PORT` | 80 | Compose |
| `GRAFANA_PORT` | 3000 | |
| `GRAFANA_ADMIN_USER` / `PASSWORD` | admin / admin | Dev default |

`.env.example` still comments OpenAI as “used in later phases”; the assistant **is** implemented — the key is simply optional.
