# Audit Logging

Sandbox records security-relevant actions to an audit log for compliance, activity feeds, and forensic review.

## How it works

```python
from app.audit.service import record_audit_event

record_audit_event(
    db,
    action="scan.run",
    user_id=membership.user_id,
    organization_id=membership.organization_id,
    resource_type="scan",
    resource_id=scan.id,
    details={"project_id": str(project_id), …},
)
```

Called from service layers after successful mutations — not from routers directly.

## Storage

Audit events are persisted and queried by:

- Organization activity feed (`/organizations/current/activity`)
- Dashboard activity panel (`/dashboard/activity`)

Model/service: `backend/app/audit/`

## Event naming convention

Dot-separated: `{domain}.{action}`

Examples: `auth.login`, `scan.run`, `report.download`, `org.member_invite`

Each feature module defines constants in `*/events.py` (e.g. `ReportAuditAction`, `ScanAuditAction`).

## Full catalog

[event-catalog.md](./event-catalog.md)

## Central definitions

`backend/app/audit/events.py` — `AuditAction` class with cross-cutting event names (auth, org, project, asset, scan, finding, report, AI).

## Activity presentation

`activity_service.py` transforms raw audit rows into human-readable timeline items with actor name, action verb, resource label, and timestamp.

Frontend: `ActivityTimeline` component shared by dashboard and activity page.

## Permissions

Reading audit/activity data requires org membership with appropriate read access. There is no separate `audit:read` permission — activity is available to members who can access the organization.

## Best practices for new features

1. Add action constants to `{feature}/events.py`
2. Call `record_audit_event` in the service layer after commit-worthy actions
3. Include `resource_type`, `resource_id`, and useful `details` (never secrets)
4. Add the action to [event-catalog.md](./event-catalog.md)
