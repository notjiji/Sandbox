# Roles and Permissions Matrix

Source of truth: `backend/app/core/permissions.py`

## Permissions

| Permission | Description |
|------------|-------------|
| `org:read` | View organization profile |
| `org:update` | Edit organization settings |
| `org:delete` | Archive/delete organization |
| `org:billing` | Billing (owner only) |
| `member:read` | List members |
| `member:invite` | Invite members |
| `member:update` | Change member roles |
| `member:remove` | Remove members |
| `member:transfer_ownership` | Transfer org ownership |
| `project:read/create/update/delete` | Project CRUD |
| `asset:read/create/update/delete` | Asset CRUD |
| `scan:read/create/run/cancel` | Scan lifecycle |
| `finding:read/review/update` | Finding workflow |
| `report:read/generate/delete` | Report library |
| `dashboard:view` | Security Intelligence dashboard |
| `ai:use` | AI Assistant |
| `monitoring:read` | View server monitoring metrics and alerts |
| `monitoring:manage` | Enroll and revoke monitoring agents |

## Role → permission summary

| Permission | owner | admin | security_analyst | manager | viewer |
|------------|:-----:|:-----:|:----------------:|:-------:|:------:|
| org:update | ✓ | ✓ | — | — | — |
| org:delete | ✓ | — | — | — | — |
| member:invite/update/remove | ✓ | ✓ | — | — | — |
| project:create/update | ✓ | ✓ | ✓ | — | — |
| asset:create/update | ✓ | ✓ | ✓ | — | — |
| scan:run | ✓ | ✓ | ✓ | — | — |
| finding:review/update | ✓ | ✓ | ✓ | — | — |
| report:generate | ✓ | ✓ | ✓ | ✓ | — |
| report:delete | ✓ | ✓ | ✓ | — | — |
| dashboard:view | ✓ | ✓ | ✓ | ✓ | ✓ |
| report:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| ai:use | ✓ | ✓ | ✓ | ✓ | — |
| monitoring:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| monitoring:manage | ✓ | ✓ | ✓ | — | — |

Owner and admin inherit all permissions except admin lacks `org:delete`, `org:billing`, and `member:transfer_ownership`.

## Feature-specific notes

### Reports

| Action | Allowed roles |
|--------|---------------|
| Generate | owner, admin, security_analyst, manager |
| View / preview / download | All roles |
| Delete | owner, admin, security_analyst |

### Dashboard

Requires `dashboard:view` — **includes viewers**. Scan execution buttons are hidden client-side for roles without `scan:run`.

### Monitoring

| Action | Allowed roles |
|--------|---------------|
| View metrics / alerts | All roles (`monitoring:read`) |
| Enroll / rotate / revoke agent | owner, admin, security_analyst (`monitoring:manage`) |

### Scans

Creating and running scans requires `scan:create` and `scan:run`. Managers and viewers can view scan history but not trigger runs.

## Changing roles

Owners and admins can PATCH `/api/v1/organizations/current/members/{id}` with a new role. Role changes take effect on the next API request (JWT role claim is refreshed on token refresh).
