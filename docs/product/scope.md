# Scope: current product vs later

This is the v1 / as-shipped boundary for **this repository**, not a marketing MVP list. “In” means implemented in backend + (usually) frontend. Stubs and catalog-only items are called out.

## In the current product

| Area | What exists |
|------|-------------|
| Auth | Register, email OTP, login, refresh, logout, password reset/change, session revoke, lockout, `X-Session-ID` |
| Users | Profile; `is_superuser` column exists (not a product role in the UI) |
| Organizations | CRUD, archive/delete (`is_active=false`; **no restore**), settings JSON, activity feed |
| Members | Invite, accept, resend, revoke, expire, role update, suspend/reactivate, remove, ownership transfer |
| Projects | CRUD, archive/restore |
| Assets | Rich types, hierarchy, links, tags, metadata, notes column, saved filters, bulk actions, timeline |
| Scans | Quick / full / custom, plugin runs, cancel, history, schedules (Celery beat) |
| Plugins (active) | http_headers, fingerprint, ssl, tls, dns, whois, ports (Nmap optional), robots, security_txt, cookies |
| CVE plugin | Enabled, included on **full** profile; looks up OSV from HTTP/service hints (not a host package inventory) |
| Findings | Normalized rows from scans (and some monitoring sources); review workflow |
| Risk | Deterministic scores at asset, project, org + history; grades A+ through F |
| Dashboard | Security intelligence for the current org |
| Reports | PDF generate/preview/download/delete; AI summary when OpenAI is configured, else offline template |
| AI chat | Org-scoped conversations, capabilities, usage tracking |
| Monitoring | Enroll/register/heartbeat/revoke; CPU/RAM/disk/network/load history; alerts vs findings |
| Audit | Meaningful events, hash chain per org, Postgres immutability trigger, list/get/export/integrity APIs, SIEM adapters |
| Event bus | In-process: persist audit → SIEM → notification stub |
| Jobs | Celery worker + beat: scans, reports, agent offline reconcile, example heartbeat |
| Observability stack | Prometheus, Grafana, Loki, Promtail, exporters in Compose; `/metrics` on the API |

## Registered but not a full product

| Item | Reality |
|------|---------|
| `cloud`, `kubernetes`, `malware` plugins | Loaded in `PluginLoader`; `enabled=False` by default |
| `admin.api_key_created` / `admin.api_key_revoked` | Catalogued audit names only; **not emitted** |
| Notifications subscriber | Logs a hook; **no email/websocket delivery** |
| Webhooks / analytics | Mentioned as future bus subscribers; **not built** |
| `org:billing` | Permission on owner; **no billing product** |

## Asset types vs coverage

Enum (`backend/app/assets/enums.py`) includes website, domain, public_ip, server, windows_server, docker_host, cloud_account, kubernetes_cluster, api_endpoint, mobile_application, git_repository, email_domain, s3_bucket, azure_subscription.

- **Scan target rule:** the caller must be an org member with scan permissions; the asset must belong to that org/project and be `active`. `website`, `domain`, and `public_ip` assets must be ownership-verified before scan.
- **Monitoring:** only `server`, `windows_server`, `docker_host`.
- Cloud / K8s / mobile / git / S3 / Azure types can be inventoried; they do **not** all have dedicated working scanners.

## Explicitly not in this codebase

- CIDR/ASN ownership allowlists and "I own this range" workflows
- Documented backup/restore runbook (manual procedures; no automated backup jobs) — [docs/deployment/backups.md](../deployment/backups.md)
- System ERD or architecture pack — **this documentation set is that pack**
- Product API keys
- In-app notification center
- Org restore after delete/archive
- Published latency/throughput SLAs

Future work is listed in [roadmap](../roadmap/README.md), not treated as shipped.
