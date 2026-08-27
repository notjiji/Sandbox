# ADR-009 — Per-organization audit hash chain

- **Status:** Accepted
- **Date:** 2026-08

## Context

Append-only audit logs need a way to detect tampering. A single global hash chain would couple all tenants and complicate exports/integrity checks per customer.

## Decision

Maintain a **SHA-256 hash chain per `organization_id`**:

- `prev_hash` / `entry_hash` on `audit_logs`
- Genesis previous hash is 64 zero hex chars for the first hashed row of each org
- Integrity API verifies the current org’s chain
- **Legacy rows with NULL hashes are skipped** during verification
- PostgreSQL trigger rejects UPDATE/DELETE on `audit_logs`

## Why

- Integrity is meaningful in a tenant context (exports, customer audits).
- Org A’s chain does not depend on Org B’s traffic.
- Skipping legacy NULL hashes allows migration without rewriting history.
- Immutability trigger raises the bar beyond application discipline alone.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Global chain | Cross-tenant coupling; painful sharding later |
| No hashing | Weaker integrity story for a security product |
| External WORM store only | Still want in-DB detectability for `/integrity` |
| Backfill hashes for all legacy rows | Risky rewrite of historical payloads |

## Consequences

- SQLite tests lack the immutability trigger (documented).
- Hash chain does not stop a DBA from dropping the trigger — ops controls still matter.
- SIEM export is separate; chain lives in Postgres first.
