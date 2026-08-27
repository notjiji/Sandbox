# Audit integrity (as built)

Naming: actions use `asset.create`; DB columns are `resource_type` / `resource_id` (API aliases `entity_*`). See [glossary.md](../glossary.md).

## Append-only

Application code does not update or delete `audit_logs`. On **PostgreSQL**, trigger `audit_logs_immutable` (Alembic `045`) raises `audit_logs are immutable` on UPDATE/DELETE.

SQLite test databases do **not** have this trigger. Unit tests may UPDATE a row to prove verification detects corruption. Production Postgres blocks that UPDATE.

## Hash chain

Hash chains are maintained **per organization**. `latest_entry_hash` and `list_chain_for_organization` both filter on `organization_id`. Org A’s first hashed row always starts at genesis, even if Org B already has events.

- `GENESIS_HASH` is 64 zero hex characters (`"0" * 64`).
- The first hashed row for an organization uses `prev_hash = GENESIS_HASH`.
- Each later row stores `prev_hash =` the previous hashed row’s `entry_hash` (same org, ordered by `created_at`, then `id`).
- `entry_hash` is SHA-256 of a canonical JSON payload that includes `prev_hash`, `id`, `organization_id`, `user_id`, `action`, `resource_type`, `resource_id`, `severity`, `details`, and `created_at`.
- Canonical `created_at` is UTC **second** precision (`replace(microsecond=0)`). The column still stores full timestamp precision.

**Legacy rows without hashes are skipped during verification.** `list_chain_for_organization` requires `entry_hash IS NOT NULL`. Rows from before migration `045` remain in the table and in search/export, but they are not part of the chain check. The first hashed row after those legacy rows still uses genesis if no earlier hashed row exists for that org.

`GET /api/v1/audit-logs/integrity` returns `{ valid, checked, broken_at, reason }` for the current organization. Tampering that changes a hashed payload yields `valid=false` and reason `entry_hash does not match canonical payload`. A broken link yields `prev_hash does not match previous entry_hash`.

Schema: Alembic `044` (`severity`) then `045` (`prev_hash` / `entry_hash` + immutability trigger).

## Fail-safe

Persist uses a SAVEPOINT. If audit insert fails, the **business transaction is still supposed to succeed**.

## SIEM

`AUDIT_SIEM_SINK` default `none`. Adapters exist for syslog, Splunk HEC, ELK, Sentinel. Unconfigured sinks do not export. This is **not** a guaranteed delivery queue.

## Access

Read/export: authenticated member with `org:read`. No public audit endpoint.
