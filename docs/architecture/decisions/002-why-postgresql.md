# ADR-002 — Why PostgreSQL

- **Status:** Accepted
- **Date:** 2026-08

## Context

Tenant data (assets, scans, findings, risk, audit) must be durable, relational, queryable with joins, and enforceable with constraints and triggers. Tests may use SQLite; production cannot.

## Decision

Use **PostgreSQL** as the system of record. Schema changes go through **Alembic**.

## Why

- Strong relational model for org → project → asset → scan → finding graphs.
- Native enums, JSONB (plugin metadata, selected plugins), and indexes we rely on.
- Supports the audit **immutability trigger** and hash-chain columns (migration `045`).
- Familiar ops story: `pg_dump`, managed Postgres, Compose volume `postgres_data`.
- Multi-tenant isolation is enforced in application queries with a single shared schema (ADR-008).

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| MongoDB / document DB | Weak joins for findings ↔ assets ↔ risk; harder integrity story |
| MySQL | Viable, but Postgres enums/JSONB/triggers match our needs better |
| SQLite in production | No concurrent write story for SaaS; no audit trigger parity |
| Per-tenant databases | Ops complexity too high for V1 modular monolith |

## Consequences

- Redis is **not** a data replica (ephemeral broker / limits only).
- SQLite is allowed for pytest convenience; production features that need triggers must be documented as Postgres-only.
- Backup strategy centers on Postgres dumps, not Redis or ephemeral volumes.
