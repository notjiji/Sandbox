# RBAC (as built)

Source of truth: `backend/app/core/permissions.py`. Org role is stored on `organization_members.role`.

Enforcement: JWT user → load **active** membership for `X-Organization-ID` → `require_permission(Permission.*)`.

## Roles

`owner`, `admin`, `security_analyst`, `manager`, `viewer`.

There is **no** fourth-party “analyst vs pentest” split. `owner` is first-class (not folded into admin).

## Permission catalog

`org:read|update|delete|billing`  
`member:read|invite|update|remove|transfer_ownership`  
`project:read|create|update|delete`  
`asset:read|create|update|delete`  
`scan:read|create|run|cancel`  
`finding:read|review|update`  
`report:read|generate|delete`  
`dashboard:view`  
`ai:use`  
`monitoring:read|manage`

## Role maps (code)

| Role | Permissions |
|------|-------------|
| owner | All of `Permission` |
| admin | All except `org:delete`, `org:billing`, `member:transfer_ownership` |
| security_analyst | Org read, member read, project read/create/update (no project delete), asset read/create/update (no asset delete), full scan + finding + report including delete, dashboard, AI, monitoring read+manage |
| manager | Read org/members/projects/assets/scans/findings, report read+generate (no delete), dashboard, AI, monitoring read |
| viewer | Read org/projects/assets/scans/findings/reports, dashboard, monitoring read. **No** member:read, **no** ai:use |

`org:billing` has **no** billing implementation behind it.

Audit list/export uses `org:read` (not a dedicated `audit:*` permission).

Full UI-oriented matrix: [docs/rbac/roles-and-permissions.md](../rbac/roles-and-permissions.md) — keep this file and that one aligned with `permissions.py`.
