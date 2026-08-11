# Organizations & Multi-Tenancy

Every project, asset, scan, and report belongs to exactly one organization. Users access org data through memberships with assigned roles.

## Core concepts

| Concept | Description |
|---------|-------------|
| Organization | Tenant with settings, branding, billing (future) |
| Membership | User ↔ org link with role and status |
| Current org | Selected via `X-Organization-ID` header on API calls |
| Project | Container for assets within an org |

## Organization API

Base: `/api/v1/organizations`

| Endpoint | Description |
|----------|-------------|
| GET `/me` | List user's organizations |
| POST `/` | Create organization |
| GET `/current` | Active org detail |
| PATCH `/current` | Update profile and settings |
| GET `/current/overview` | Legacy/summary overview |
| GET `/current/activity` | Paginated audit activity |
| GET `/current/reports` | Org-wide report library |
| GET `/current/dashboard/*` | Security dashboard |
| PATCH `/current/archive` | Archive org |
| DELETE `/current` | Soft-delete org |

## Settings (JSONB)

Stored in `organizations.settings`:

```json
{
  "language": "en",
  "notifications": { "email_enabled": true, "weekly_reports": true, … },
  "security": { "mfa_policy": "optional", … },
  "branding": { "primary_color": "#7c3aed", "contact_email": "…", "footer_text": "…" }
}
```

Logo URL is a top-level column: `organizations.logo_url`.

Branding flows into PDF reports — see [../reports/templates.md](../reports/templates.md).

## Members & invites

Documented alongside organizations:

| Action | Permission |
|--------|------------|
| Invite member | `member:invite` |
| Accept invite | Public/authenticated accept flow |
| Update role | `member:update` |
| Remove member | `member:remove` |
| Transfer ownership | `member:transfer_ownership` |

API: `/api/v1/organizations/current/members`

Roles: see [../rbac/roles-and-permissions.md](../rbac/roles-and-permissions.md)

## Frontend flows

| Route | Purpose |
|-------|---------|
| `/select-organization` | Pick active org after login |
| `/organization/settings` | General, branding, security, notifications |
| `/organization/members` | Member management |
| `/organization/activity` | Audit timeline |

Active org ID stored in `orgStorage` (`frontend/src/features/organizations/storage.ts`).

## Data isolation

All repositories scope queries by `organization_id` derived from membership. Cross-org access is rejected at the service layer.

## Key files

| Layer | Path |
|-------|------|
| Models | `backend/app/organizations/models.py` |
| Service | `backend/app/organizations/services/organization_service.py` |
| Members | `backend/app/members/` |
| Org scope helper | `backend/app/shared/db/org_scope.py` |
| Frontend | `frontend/src/features/organizations/` |

## Demo data

Pre-seeded orgs and roles: [../demo-data.md](../demo-data.md)
