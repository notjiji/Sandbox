# ADR-008 — Multi-tenant organization isolation

- **Status:** Accepted
- **Date:** 2026-08

## Context

Sandbox is multi-tenant SaaS. Users may belong to multiple organizations. Cross-tenant reads/writes are a critical security failure.

## Decision

- **Shared database, shared schema**, logical isolation by `organization_id`.
- Every org-scoped request requires `X-Organization-ID` plus an **active membership**.
- Services resolve membership first, then query with org (and project) scope.
- Roles (RBAC) gate actions inside the tenant; they do not replace tenancy checks.

## Why

- One Postgres to operate (ADR-002) while still isolating tenants in application code.
- Membership model supports multi-org users cleanly.
- Testable: org A must not read org B assets, scans, findings, reports, AI, audit, monitoring.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Database-per-tenant | Provisioning and migration cost |
| Postgres RLS as sole control | Still want explicit service checks; RLS alone is easy to bypass in raw SQL paths |
| Subdomain-only tenancy without header | Harder for API clients; we standardize on header + membership |

## Consequences

- Bugs that omit `organization_id` filters are security bugs — isolation tests are mandatory.
- No claim of physical isolation or per-tenant encryption keys in V1.
- Spoofing `X-Organization-ID` without membership must fail (403).
