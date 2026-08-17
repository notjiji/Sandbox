# Frontend

React 19 + TypeScript + Vite 6 + Tailwind. Package: `frontend/` (`sandbox-frontend`).

In Compose, nginx serves the SPA and proxies `/api/v1` to the backend. The frontend build uses `VITE_API_BASE_URL=/api/v1`.

## Routing (`frontend/src/app/routes/index.tsx`)

Public: `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/accept-invite`.

Authenticated: `/select-organization`, `/welcome`, `/profile`, `/settings`.

Org-scoped (`OrgProtectedRoute`): dashboard, org settings, activity, members, projects, assets, scans, findings, reports, asset monitoring, AI assistant.

## API usage

- TanStack Query for server state.
- Org-scoped calls send `Authorization: Bearer` and `X-Organization-ID`.
- Feature clients live under `frontend/src/features/*/api.ts`.

## Auth UX

Login/register/verify match the auth API. Organization picker is required when the user has multiple memberships. Role-gated actions (for example scan run) are hidden when the permission is missing; **the API still enforces RBAC**.

## What the UI does not include

- Billing
- API key management
- Webhook or SIEM configuration screens (`AUDIT_SIEM_SINK` is env-only)
- A dedicated “audit log” product page separate from Activity (activity is the operator feed; full audit list/export is API + activity export CSV/PDF)
