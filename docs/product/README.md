# Product

As-built description of Sandbox. This folder is the product source of truth: it records what the platform **does today**, not a target spec.

If a feature README under `docs/auth/`, `docs/scans/`, and similar disagrees with these pages, treat this folder as correct until that deep-dive is updated.

Canonical naming (events, roles, statuses, `resource_*` vs `entity_*`): [glossary.md](../glossary.md).

| Document | Covers |
|----------|--------|
| [Definition](./definition.md) | Product, problem, solution, target users, V1 vs Future |
| [Goal](./goal.md) | What Sandbox is for |
| [Users](./users.md) | Roles and who uses the product |
| [Use cases](./use-cases.md) | Core workflows that exist in the UI and API |
| [Scope](./scope.md) | In the current product vs later / stubbed |
| [Functional requirements](./functional-requirements.md) | Numbered V1 shall-statements (FR-*) |
| [Non-functional requirements](./non-functional-requirements.md) | Numbered NFR-* : security, performance, scale, availability, maintainability |

Related: [architecture](../architecture/README.md), [security](../security/README.md), [roadmap](../roadmap/README.md).
