# Audit integrity (as built)

## Append-only

Application code does not update or delete `audit_logs`. On **PostgreSQL**, trigger `audit_logs_immutable` raises `audit_logs are immutable` on UPDATE/DELETE (Alembic `045`).

SQLite test databases do not have this trigger.

## Hash chain

Per **organization**:

- `entry_hash` = SHA-256 of a canonical payload including previous hash
- `prev_hash` of the first hashed row is 64 zero hex chars
- Rows created before 045 may have NULL hashes; integrity verify **skips** those
- Canonicalization uses microsecond precision in the hash payload; `created_at` is stored at full precision

`GET /api/v1/audit-logs/integrity` reports chain status for the current org.

## Fail-safe

Persist uses a SAVEPOINT. If audit insert fails, the **business transaction is still supposed to succeed**.

## SIEM

`AUDIT_SIEM_SINK` default `none`. Adapters exist for syslog, Splunk HEC, ELK, Sentinel. Unconfigured sinks do not export. This is **not** a guaranteed delivery queue.

## Access

Read/export: authenticated member with `org:read`. No public audit endpoint.
