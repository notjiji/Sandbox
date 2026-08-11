# Dashboard Architecture

## Data flow

```
Dashboard.tsx
    → useSecurityDashboard hooks (TanStack Query)
    → /organizations/current/dashboard/*
    → dashboard/service.py
    → dashboard/repository.py
    → projects, assets, findings, scans, risk, audit tables
```

## Design principles

1. **Org-scoped only** — Every query filters by `membership.organization_id`.
2. **Read-only aggregation** — Dashboard never mutates data; it composes existing domain services.
3. **Graceful degradation** — `@dashboard_operation` wrapper returns safe empty payloads on partial failures instead of 500s.
4. **No caching layer (V1)** — TanStack Query handles client-side stale/refetch; backend hits DB directly.

## Module layout

| File | Role |
|------|------|
| `router.py` | Six GET endpoints, all require `DASHBOARD_VIEW` |
| `service.py` | Business logic, calls repository + risk helpers |
| `repository.py` | SQL aggregation queries |
| `schemas.py` | Pydantic response models |
| `errors.py` | `DashboardUnavailableError` for controlled failures |

## Score source

Dashboard security score comes from organization risk history (`OrganizationRisk` / `OrganizationRiskHistory`), not a client-side calculation. See [../risk/scoring-model.md](../risk/scoring-model.md).

## Primary project

`overview.primary_project_id` identifies the first active project in the org. Used for navigation shortcuts (assets, findings, scan links) when the user has not selected a project context in the sidebar.

## Frontend state

Each panel is an independent TanStack Query with shared invalidation via `dashboardKeys.all`. The page shows skeleton loaders per-panel so one slow endpoint does not block the entire view.

## Testing

`backend/tests/test_dashboard.py` covers:

- Auth required
- Cross-org isolation
- Viewer can read dashboard
- Viewer cannot run scans (RBAC on scan endpoints, not dashboard itself)
