# Audit Logging

Sandbox records **meaningful events only** — not every request — for compliance, the activity feed, and forensic search.

## How it works

Every feature uses the same write path. Audit failure never rolls back the business action.

```python
from app.audit.service import audit_service

audit_service.log(
    db,
    organization_id=org_id,
    user_id=user_id,
    action="asset.create",
    entity_type="asset",
    entity_id=asset.id,
    severity="info",  # optional; inferred from the action when omitted
    details={"asset_name": asset.name, "asset_type": "website"},
)
```

`record_audit_event(...)` is the same method (used by existing call sites). Writes run in a SAVEPOINT so a failed insert cannot abort the outer transaction.

Event names are **dot-separated** (`asset.create`), not `ASSET_CREATED`. See [event-catalog.md](./event-catalog.md) for the mapping.

## Storage

Table `audit_logs`:

| Field | Type |
|-------|------|
| id | UUID |
| organization_id | UUID |
| user_id | UUID |
| action | VARCHAR |
| resource_type | VARCHAR (`entity_type` in APIs) |
| resource_id | UUID (`entity_id` in APIs) |
| severity | VARCHAR (`info` / `warning` / `error` / `critical`) |
| details | JSONB |
| ip_address | VARCHAR |
| user_agent | TEXT |
| created_at | TIMESTAMP |

`entity_type` / `entity_id` are API aliases of `resource_type` / `resource_id`. Column names are unchanged so existing rows stay valid.

## Severity

| Level | Examples |
|-------|----------|
| INFO | Asset created, login success, invite, report generated |
| WARNING | Scan failed, login failure, member removed |
| ERROR | Plugin failed |
| CRITICAL | Admin account disabled, account locked |

Defaults live in `backend/app/audit/constants.py`. Callers can override.

## Search

Forensic (includes auth events):

`GET /api/v1/organizations/current/audit-logs`

Activity feed (excludes `auth.*` and `user.*`):

`GET /api/v1/organizations/current/activity`

Shared filters from day one:

- `date_from` / `date_to`
- `action` (exact, or `scan.*` for a prefix)
- `user_id`
- `actor` (name or email, e.g. Amine)
- `asset_id`
- `severity`
- `entity_type` / `entity_id` (audit-logs only)
- `organization` is implied by the current org membership header

Examples:

- Scan failures last 30 days: `action=scan.failed&date_from=<iso>`
- All actions by Amine: `actor=Amine`

## Activity feed

The dashboard and organization Activity page consume the same audit rows, presented as human-readable messages:

- Scan completed on vinca.family
- New asset added (`added asset {name}`)
- Technical report generated
- User invited to organization

## Permissions

`org:read`. There is no separate `audit:read` permission.

## Best practices

1. Log only catalog events — not heartbeats, list GETs, or token refresh noise for the feed
2. Call `audit_service.log` / `record_audit_event` after the mutation is ready to commit
3. Include `entity_type`, `entity_id`, and useful `details` (never passwords, tokens, or API keys)
4. Do not wrap business logic in try/except around audit — the service already swallows write errors
5. Add new actions to `{feature}/events.py` and [event-catalog.md](./event-catalog.md)
