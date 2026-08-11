# Security Intelligence Dashboard

The dashboard is the organization-level home screen showing security posture at a glance. All data is loaded from the backend — no hardcoded scores or findings.

## What it shows

| Panel | Data |
|-------|------|
| Security score | Current org score, grade, change vs previous |
| Risk trend | Historical score chart |
| Findings by severity | Breakdown + top critical findings |
| Asset overview | Counts by type (websites, domains, IPs, servers) |
| Top risky assets | Lowest-scoring or highest-risk assets |
| Upcoming scans | Scheduled scan runs |
| Activity | Recent audit events |

## Access

- **Route:** `/dashboard` (frontend)
- **Permission:** `dashboard:view` (all org roles including viewer)
- **API prefix:** `/api/v1/organizations/current/dashboard`

## Related docs

- [architecture.md](./architecture.md) — backend aggregation design
- [api.md](./api.md) — endpoint reference
- [../risk/README.md](../risk/README.md) — how scores are calculated

## Key files

| Layer | Path |
|-------|------|
| Backend router | `backend/app/dashboard/router.py` |
| Service | `backend/app/dashboard/service.py` |
| Repository | `backend/app/dashboard/repository.py` |
| Frontend page | `frontend/src/features/organizations/pages/Dashboard.tsx` |
| Hooks | `frontend/src/features/dashboard/hooks/useSecurityDashboard.ts` |
| Components | `frontend/src/features/organizations/components/dashboard/` |

## Actions from dashboard

- **Run Scan** — links to project assets (requires `scan:run`)
- **Generate Report** — opens report modal (requires `report:generate`)
- **Findings cards** — deep-link to findings with `?severity=critical`
