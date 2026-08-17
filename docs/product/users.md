# Target users

Users are **global accounts**. Access to tenant data comes from an **organization membership** with one of five roles. Source: `backend/app/core/permissions.py` and `backend/app/members/enums.py`.

## Roles

| Role | Product intent | In the product |
|------|----------------|----------------|
| `owner` | Full control of the tenant, including delete and ownership transfer | Yes. Also the only role with `org:billing` (no billing UI yet). |
| `admin` | Day-to-day administration without org delete, billing, or ownership transfer | Yes |
| `security_analyst` | Run scans, review findings, manage monitoring agents, generate/delete reports | Yes |
| `manager` | Read-mostly plus generate reports and use AI; cannot run scans or mutate assets | Yes |
| `viewer` | Read dashboard, assets, scans, findings, reports, monitoring | Yes. No `ai:use`. |

The permission matrix lives in [security/rbac](../security/rbac.md). Feature deep-dive: [docs/rbac/roles-and-permissions.md](../rbac/roles-and-permissions.md).

## Who these roles map to in practice

| Persona | Typical role | What they do in Sandbox |
|---------|--------------|-------------------------|
| Founder / security lead | owner | Create org, invite people, org settings, transfer ownership |
| Platform / IT admin | admin | Members, projects, assets, scans |
| Security engineer | security_analyst | Scan, triage findings, enroll agents, generate reports |
| Engineering or compliance manager | manager | Read posture, generate reports, ask AI |
| Auditor / stakeholder | viewer | Read-only dashboards and reports |

A user can belong to **multiple organizations** with different roles. After login they pick an org (`/select-organization`) unless they have exactly one.

## Demo accounts

Seeded by `make seed`. Password for all: `DemoPassword1!`. Org: Demo Corp (`demo-corp`).

| Email | Role |
|-------|------|
| `owner@demo.sandbox` | owner |
| `admin@demo.sandbox` | admin |
| `analyst@demo.sandbox` | security_analyst |
| `manager@demo.sandbox` | manager |
| `viewer@demo.sandbox` | viewer |

Details: [docs/demo-data.md](../demo-data.md).
