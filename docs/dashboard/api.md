# Dashboard API

Base: `/api/v1/organizations/current/dashboard`

**Headers:** `Authorization: Bearer …`, `X-Organization-ID: …`

**Permission:** `dashboard:view`

## Endpoints

### GET `/overview`

Primary payload for the dashboard header and summary cards.

```json
{
  "score": { "current": 72, "previous": 81, "change": -9, "grade": "C", "trend": "declining" },
  "assets": { "total": 14, "websites": 8, "domains": 3, "ips": 2, "servers": 1 },
  "findings": { "critical": 2, "high": 7, "medium": 13, "low": 5, "info": 0 },
  "last_scan": { "status": "completed", "timestamp": "…", "asset_name": "…", "project_id": "…" },
  "primary_project_id": "uuid",
  "scanned_assets": 10,
  "unscanned_assets": 4,
  "assets_at_risk": 3,
  "trend": "declining"
}
```

### GET `/risk-trend`

Historical organization scores for the trend chart.

Query: none

Response: `{ "history": [{ "date": "…", "score": 81.0, "grade": "B" }, …] }`

### GET `/findings-summary`

Query: `limit` (1–20, default 5)

Response: severity breakdown + top critical/high findings with asset context.

### GET `/top-assets`

Query: `limit` (1–20, default 5)

Response: assets sorted by risk (lowest score / highest exposure first).

### GET `/activity`

Query: `limit` (1–50, default 10)

Response: recent audit events formatted for the dashboard Activity Feed card (`ActivityFeedCard`).

### GET `/upcoming-scans`

Query: `limit` (1–50, default 10)

Response: scheduled scans with `next_run_at`, asset name, scan type.

## Error handling

Partial endpoint failures return empty collections with HTTP 200 where possible. Hard auth/permission failures return 401/403.

## Frontend hooks

| Hook | Endpoint |
|------|----------|
| `useDashboardOverview` | `/overview` |
| `useDashboardRiskTrend` | `/risk-trend` |
| `useDashboardFindingsSummary` | `/findings-summary` |
| `useDashboardTopAssets` | `/top-assets` |
| `useDashboardActivity` | `/activity` |
| `useDashboardUpcomingScans` | `/upcoming-scans` |

Defined in `frontend/src/features/dashboard/hooks/useSecurityDashboard.ts`.
