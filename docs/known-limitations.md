# Known limitations

This document states **current boundaries** of the Sandbox platform as built in this repository. It is intentional honesty for operators, auditors, and engineers — not a roadmap wishlist.

Deeper security notes: [security/known-limits.md](./security/known-limits.md).  
Deployment gaps: [deployment/backups.md](./deployment/backups.md).  
Future work: [roadmap/](./roadmap/README.md).

---

## Scanning and authorization

- **Nmap service/version detection is optional.** The ports plugin runs TCP checks in Python. `nmap -sV` is used only when `nmap` is on PATH (the backend image installs it in Compose). Missing Nmap does not fail the scan; version detection is simply absent.
- **Scanner authorization is org-scoped plus ownership verification for selected types.** A scan requires auth, org membership, permissions, an org/project asset with `status=active`, and — for `website`, `domain`, and `public_ip` — `verification_status=verified` (domain / DNS TXT / HTTP / IP challenge flows). Other asset types are not forced through verification unless a challenge is configured. There is still **no** CIDR/ASN ownership allowlist or “I own this IP range” product. Treat operators as responsible for scanning only infrastructure they control.
- **Inventory ≠ full coverage.** Asset types such as mobile, git, S3, Azure, and much of cloud/Kubernetes can be stored; they do not all have dedicated working scanners.
- **Cloud, Kubernetes, and malware plugins** are registered but default `enabled=False`.
- **CVE plugin** is hint-based OSV lookup from HTTP/service signals — not authenticated host package inventory, KEV feeds, or exploit correlation.

## Product features not built

- **Webhooks are not implemented.** The event bus can grow subscribers; there is no outbound webhook delivery product.
- **Analytics event consumers are not implemented.** Dashboard summaries exist; there is no BI pipeline, product analytics warehouse, or third-party analytics sink.
- **Notifications** — the bus subscriber logs a hook only; no email/in-app notification center or websocket push product.
- **API keys / machine auth** — audit action names are reserved; keys are not issued.
- **Billing** — `org:billing` exists on the owner role; there is no billing product.
- **Organization restore** after archive/delete is not available.
- **Product UI for SIEM** — SIEM export is env-configured (`AUDIT_SIEM_SINK`); Activity is not a full SIEM console.

## AI

- **AI depends on configured provider availability.** Live chat and report AI summaries require `OPENAI_API_KEY`. When empty or the provider is down, chat degrades and report summaries use an offline template. Core scan → findings → risk → PDF layout still works without AI.

## Audit and integrity

- **Legacy audit records may not contain hash-chain values.** Rows created before migration `045` can have NULL `prev_hash` / `entry_hash`. Integrity verification **skips** those rows; it does not invent hashes for them.
- **Hash chains are per organization**, not global.
- **Immutability trigger is PostgreSQL-only.** SQLite test databases do not enforce UPDATE/DELETE rejection on `audit_logs`.
- Hash chain integrity detects tampering of hashed rows; it does not stop a DBA from dropping the trigger.

## Dashboard and UX

- **Finding/scan trend visualization on the main dashboard is limited.** Scan history and finding-trend APIs exist with 7d/30d/90d/1y ranges, but charts are simplified (intensity strips / compact tables), not a full interactive multi-series analytics suite.
- Risk trend is historical score points rendered as a simple bar strip — adequate for posture glance, not a full time-series BI tool.

## Platform and operations

- **Automated Postgres backups** via `infrastructure/backup/` service (daily, encrypted, 7-day retention, monthly restore test). See [deployment/backups.md](./deployment/backups.md).
- **Redis is ephemeral** — Celery broker, rate limits, lockout counters. It is not durable business data and is not part of the backup policy as a system of record.
- **Compose is development-oriented** — uvicorn `--reload`, bind mounts, default Grafana `admin`/`admin`, plain HTTP on port 80. Production hardening is operator-owned ([deployment/production.md](./deployment/production.md)).
- **No published performance or uptime SLA** in this repository.
- **No frontend automated test suite** (typecheck/build only in V1).
- **`users.is_superuser`** exists in the schema but is not a documented product RBAC path in the UI.
- **Email (Resend)** — production requires `RESEND_API_KEY` at boot; there is no mail delivery SLA. Without a key in development, OTP email may not send (use seed/demo users).

## Testing honesty

- CI runs pytest, frontend build, production Docker build, secret/inventory checks, staging acceptance, and a database restore drill on every PR — [deployment/ci.md](deployment/ci.md). Green CI does **not** prove frontend e2e, live OpenAI, live DNS/HTTP against the public internet, or load tests. Fast pytest still uses SQLite; the restore drill and staging jobs use Compose Postgres.

---

## How to use this document

| Audience | Use |
|----------|-----|
| Operators | Know what you must provide (backups, TLS, secrets, Nmap image, OpenAI, SIEM) |
| Security reviewers | Do not assume CIDR allowlists, API keys, or perfect audit backfill |
| Product / sales | Do not sell disabled plugins or webhook/analytics consumers as shipped |
| Engineers | Prefer extending real gaps over re-documenting wishlist items as done |

When a limitation is removed, update this file, the matching FR/NFR if any, and [roadmap/known-limitations.md](./roadmap/known-limitations.md) in the same change.
