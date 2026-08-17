# Production constraints (code, not a full runbook)

`Settings.validate_production_settings` when `ENVIRONMENT=production`:

1. `SECRET_KEY` / `JWT_SECRET` must not start with `change-me`
2. `POSTGRES_PASSWORD` must not contain `changeme` (any case)
3. `RESEND_API_KEY` must be set

Also: OpenAPI `/docs` and `/redoc` are `None`. `SCAN_RUN_INLINE` and `REPORT_RUN_INLINE` default **false**.

## Not provided by this repo

- A production Compose/K8s overlay
- TLS certificates
- Hardened Grafana (change default admin)
- Database backups, PITR, or offsite copies
- SIEM on by default (`AUDIT_SIEM_SINK=none`)
- Horizontal scaling guide

Treat current `docker-compose.yml` as **development**. Production is “set ENVIRONMENT=production and satisfy the validator,” plus whatever you add outside this repository.
