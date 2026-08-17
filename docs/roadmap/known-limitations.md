# Known limitations

Aligned with the current code (Alembic head `045_audit_log_hash_chain`).

## Product

- No API-key machine users (audit action names reserved only)
- No webhook delivery
- No notification email/websocket delivery (bus subscriber logs only)
- No billing product despite `org:billing`
- No org restore after archive/delete
- No third-party / IP-ownership scan authorization
- Asset types exist that lack first-class scanners (mobile, git, much of cloud/K8s)
- Cloud, kubernetes, malware plugins registered but `enabled=False`
- CVE plugin is hint + OSV, not authenticated host inventory
- Nmap is optional and environment-dependent
- Activity UI is not a full SIEM console; SIEM export is opt-in env

## Platform

- Root README was empty before this documentation set; feature READMEs can lag code (AI `ai.chat`, risk grade table missing A+)
- No backup/restore
- No published performance SLA
- No frontend automated tests
- Compose is a dev stack (reload, default Grafana credentials)
- Audit immutability trigger is Postgres-only
- `users.is_superuser` is unused as a documented product role

## Docs that were wrong or missing before this pack

- `docs/architecture/` and `docs/database/` were placeholders
- Checklist items that described additive “penalty display” risk or four roles without `owner` do not match `permissions.py` / `scoring.py`
- Scan target validation is **active org asset**, not an allowlist
