# Audit Logging

Sandbox records **meaningful events only** — not every request — for compliance, the activity feed, forensic search, and SIEM export.

## Event bus

Feature modules publish once. Subscribers handle side effects independently:

```
event_bus.publish("ASSET_CREATED", payload, db=db, organization_id=org_id, user_id=user_id, entity_type="asset", entity_id=asset.id)
        │
        ├── Audit Logger (hash-chained row)
        ├── SIEM export (syslog / Splunk / ELK / Sentinel)
        ├── Notifications (hook; delivery comes later)
        └── Future webhooks / analytics
```

`record_audit_event` / `audit_service.log` publish on the same bus, so existing call sites do not need to change. A failing subscriber never aborts the business action.

```python
from app.events import event_bus

event_bus.publish(
    "ASSET_CREATED",
    {"asset_name": asset.name, "asset_type": "website"},
    db=db,
    organization_id=org_id,
    user_id=user_id,
    entity_type="asset",
    entity_id=asset.id,
)
```

Event names are **dot-separated** (`asset.create`). `ASSET_CREATED` and `SCAN_COMPLETED` are accepted as aliases. See [event-catalog.md](./event-catalog.md).

## Tamper resistance

Rows are **append-only**. Application code never updates or deletes `audit_logs`. PostgreSQL trigger `audit_logs_immutable` (Alembic `045`) rejects UPDATE and DELETE. SQLite tests do not install that trigger.

**Hash chains are maintained per organization.** Org A and Org B never share `prev_hash` links. The first hashed event in each organization uses genesis (`prev_hash` = 64 zero hex characters).

Each hashed row stores:

- `prev_hash` — previous hashed row’s `entry_hash` in the same organization (or genesis)
- `entry_hash` — SHA-256 of canonical JSON including `prev_hash` and the event payload. Canonical `created_at` is UTC second precision (`replace(microsecond=0)`).

**Legacy audit records without hashes are skipped during verification.** `list_chain_for_organization` loads only rows with `entry_hash IS NOT NULL`. Pre-`045` rows stay searchable and exportable; integrity does not recompute them.

Verified flow:

```
create event → persist writes entry_hash
             → next event.prev_hash == previous entry_hash
             → GET /audit-logs/integrity  valid=true
             → (SQLite only) mutate a hashed row → valid=false
```

`GET /api/v1/audit-logs/integrity` re-computes the chain for the current organization only. See [security/audit.md](../security/audit.md).

## Storage

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
| prev_hash | VARCHAR(64) |
| entry_hash | VARCHAR(64) |
| created_at | TIMESTAMP |

## API

Org-scoped via `X-Organization-ID`. Permission: `org:read`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/audit-logs` | Search |
| GET | `/api/v1/audit-logs/{id}` | Single record |
| GET | `/api/v1/audit-logs/export?format=csv\|pdf` | Download |
| GET | `/api/v1/audit-logs/integrity` | Hash-chain check |

The same list/export/get routes are also mounted at `/api/v1/organizations/current/audit-logs`.

Filters: `action` (`scan.completed` or `SCAN_COMPLETED`), `severity`, `user_id`, `actor`, `asset_id`, `date_from`, `date_to`, `entity_type`, `entity_id`.

Activity feed (hides `auth.*` / `user.*`): `GET /api/v1/organizations/current/activity`.

## SIEM export

Set `AUDIT_SIEM_SINK` to `syslog`, `splunk`, `elk`, or `sentinel`. Default `none`. Export is best-effort after the row is written; a sink outage does not fail the API.

## Dashboard

The Security Intelligence dashboard **Recent Activity** card reads the activity endpoint and shows compact check / warning rows (scan completed, asset added, report generated, scan failed, user invited).

## Best practices

1. Publish catalog events — not heartbeats or list GETs
2. Prefer `event_bus.publish`; `audit_service.log` is the same bus
3. Include `entity_type`, `entity_id`, and useful `details` (never passwords, tokens, or API keys)
4. Do not wrap business logic around audit/SIEM errors
5. Add new actions to `{feature}/events.py` and [event-catalog.md](./event-catalog.md)
