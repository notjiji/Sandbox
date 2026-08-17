# Multi-tenancy (as built)

## Tenant key

One Postgres schema for all tenants. Isolation is **logical**:

- `X-Organization-ID` selects the tenant.
- `organization_members` must exist and be active for that user+org.
- Domain rows carry `organization_id` and/or `project_id` with FKs. Lookups go through membership-aware services (for example `require_org_asset`, project `require_active_project`).

## Cross-tenant access

A token from org A with header org B only works if the user is an active member of B. IDs from another org should 404/403 via scoped queries. Regression tests: `backend/tests/test_org_isolation.py`.

## Not used

- Separate database or schema per org
- Row-level security policies in Postgres (application-enforced)
- Shared “global assets” across orgs

## Org lifecycle

Archive/delete sets `is_active=false` (and `deleted_at` on delete path). **No restore.** Members are removed (hard delete of membership rows), not tombstoned as a product restore flow.
