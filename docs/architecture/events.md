# Events and audit pipeline

In-process bus: `backend/app/events/bus.py`. Not Kafka, not Redis pub/sub.

## Publish

```python
event_bus.publish(
    "asset.create",  # or alias ASSET_CREATED → normalized
    payload,
    db=db,
    organization_id=org_id,
    user_id=user_id,
    entity_type="asset",  # stored as resource_type
    entity_id=asset.id,
)
```

`record_audit_event` / `audit_service.log` publish on the **same** bus.

Names: dot-separated `{domain}.{action}`. Aliases: `backend/app/events/names.py`.

## Subscribers (order registered)

1. `persist_audit_event` — write `audit_logs` with prev/entry SHA-256 (per organization). Genesis previous hash is 64 zeros. Fail-safe SAVEPOINT.
2. `forward_audit_to_siem` — `AUDIT_SIEM_SINK=none|syslog|splunk|elk|sentinel`. Default **none**.
3. `on_domain_event` — if action in `{scan.completed, scan.failed, org.member_invite, report.generate, monitoring.alert_opened}`, **log** `notification hook`. No send.

Each handler is wrapped in try/except so one failure does not skip the rest.

## What is not on the bus yet

Webhooks and analytics are comments/future, not modules. API-key events are constants only.

## Activity feed vs audit API

- Activity: `GET .../organizations/current/activity` — operator timeline, **excludes** `auth.*` and `user.*`.
- Audit: `GET /api/v1/audit-logs` — searchable log including auth events; CSV/PDF export; `/integrity` verifies the hash chain.

Details: [docs/audit/README.md](../audit/README.md).
