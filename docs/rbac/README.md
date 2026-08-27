# Role-Based Access Control (RBAC)

Sandbox uses organization-scoped roles mapped to fine-grained permissions. Every API request (except public auth routes) requires authentication and, for org resources, an active membership.

## Concepts

| Concept | Description |
|---------|-------------|
| **User** | Global account; can belong to multiple organizations |
| **Organization** | Tenant boundary; all projects/assets/scans live inside an org |
| **Membership** | Links user + org + role + status |
| **Permission** | Atomic capability (e.g. `scan:run`, `report:read`) |
| **Role** | Named bundle of permissions assigned to a member |

## Organization roles

| Role | Purpose |
|------|---------|
| `owner` | Full control including billing, org delete, ownership transfer |
| `admin` | Full operational control except billing, org delete, ownership transfer |
| `security_analyst` | Run scans, review findings, generate/delete reports |
| `manager` | Read-mostly + generate reports; no scan execution |
| `viewer` | Read-only access including dashboard and reports |

Canonical wire values (and UI labels): [glossary.md](../glossary.md). See [roles-and-permissions.md](./roles-and-permissions.md) for the full matrix.

## Enforcement

```
HTTP Request
    → Bearer access token (JWT)
    → X-Organization-ID header
    → get_current_user + load OrganizationMember
    → require_permission(Permission.X)
    → route handler
```

**Key files:**

- `backend/app/core/permissions.py` — permission enum and role maps
- `backend/app/core/rbac.py` — helper utilities
- `backend/app/api/deps.py` — `require_permission()`, `get_current_user()`
- `backend/app/members/enums.py` — `OrganizationRole`, `MemberStatus`

## Frontend gating

The UI mirrors backend roles via `useOrganizationRole()`:

- `canRunScan` — owner, admin, security_analyst
- `canGenerateReport` — owner, admin, security_analyst, manager
- `canDeleteReport` — owner, admin, security_analyst
- `canManage` — owner, admin
- `canManageMonitoring` — owner, admin, security_analyst

Never rely on UI alone; the API always re-checks permissions.

## Org isolation

Members only access data belonging to their organization. Cross-org access attempts return 404 or 403. Integration tests in `backend/tests/test_org_isolation.py` and feature-specific RBAC tests (e.g. `test_dashboard.py`, `test_reports_rbac.py`) verify this.

## Diagram

See [../diagrams/enforcement mechanism.png](../diagrams/enforcement%20mechanism.png).
