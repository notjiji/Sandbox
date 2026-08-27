# Architecture Decision Records

ADRs capture **engineering judgment**: why the system is shaped this way, what was rejected, and what trade-offs we accept.

| ID | Title | Status |
|----|-------|--------|
| [ADR-001](./001-why-fastapi.md) | Why FastAPI | Accepted |
| [ADR-002](./002-why-postgresql.md) | Why PostgreSQL | Accepted |
| [ADR-003](./003-why-celery.md) | Why Celery | Accepted |
| [ADR-004](./004-plugin-based-scanner.md) | Plugin-based scanner architecture | Accepted |
| [ADR-005](./005-deterministic-risk-scoring.md) | Deterministic risk scoring | Accepted |
| [ADR-006](./006-ai-separated-from-scanning.md) | AI separated from scanning | Accepted |
| [ADR-007](./007-event-driven-audit.md) | Event-driven audit architecture | Accepted |
| [ADR-008](./008-multi-tenant-org-isolation.md) | Multi-tenant organization isolation | Accepted |
| [ADR-009](./009-per-org-audit-hash-chain.md) | Per-organization audit hash chain | Accepted |
| [ADR-010](./010-modular-monolith.md) | Modular monolith over microservices | Accepted |

## Template

Each ADR uses:

1. **Context** — problem and forces  
2. **Decision** — what we chose  
3. **Why** — rationale  
4. **Alternatives** — options considered  
5. **Consequences** — benefits and costs  

## Rules

- ADRs are **immutable history**. To reverse a decision, add a new ADR that supersedes the old one; do not rewrite the past.
- Status values: `Proposed` · `Accepted` · `Superseded` · `Deprecated`.
- Keep ADRs short. Deep how-to belongs in architecture and feature docs, not here.

Related: [architecture README](../README.md), [known limitations](../../known-limitations.md).
