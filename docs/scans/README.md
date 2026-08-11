# Scans

Scans execute security plugins against assets and produce findings. This document is an index — the full pipeline is documented in [../scan-engine.md](../scan-engine.md).

## Lifecycle

```
pending → queued → running → completed | failed | cancelled
```

Managed by `backend/app/scans/lifecycle.py` and `scan_service.py`.

## API

Asset scope: `/api/v1/projects/{project_id}/assets/{asset_id}/scans`

| Action | Permission |
|--------|------------|
| List / get | `scan:read` |
| Create | `scan:create` |
| Run | `scan:run` |
| Cancel | `scan:cancel` |

## Scan types & profiles

| Type | Description |
|------|-------------|
| `QUICK` | Fast subset of plugins |
| `FULL` | All active plugins |
| `CUSTOM` | User-selected plugins |

Profiles: `backend/app/scans/profiles.py`

## Schedules

Recurring scans use cron schedules checked every minute by Celery Beat (`check_due_schedules`). Schedule CRUD is part of the scans module.

## Async execution

| Mode | Setting | Behavior |
|------|---------|----------|
| Inline (dev) | `SCAN_RUN_INLINE=true` | Runs in API process |
| Queued (prod) | `SCAN_RUN_INLINE=false` | Celery `execute_scan` task |

See [../jobs/README.md](../jobs/README.md).

## Persistence

| Table | Contents |
|-------|----------|
| `scans` | Scan record, status timestamps, selected plugins |
| `scan_plugin_runs` | Per-plugin status, duration, findings count |
| `findings` | Normalized issues from the scan |

## Frontend

Route: `/projects/:projectId/assets/:assetId/scans`

## Related

- [../plugins/README.md](../plugins/README.md)
- [../findings/README.md](../findings/README.md)
- [../scan-engine.md](../scan-engine.md)
