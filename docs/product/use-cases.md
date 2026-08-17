# Core use cases

These workflows exist in the current UI (`frontend/src/app/routes/index.tsx`) and API (`/api/v1`). Paths are frontend unless noted.

## Account and tenant

1. **Register and verify email** — `/register`, OTP via email (`/verify-email`). Production requires Resend.
2. **Sign in, refresh, lockout** — `/login`. Failed attempts can lock the account. Sessions are revocable (`X-Session-ID`).
3. **Reset password** — `/forgot-password`, `/reset-password`.
4. **Create or join an organization** — create on `/welcome`; join via `/accept-invite`.
5. **Select organization** — `/select-organization`. Subsequent API calls send `X-Organization-ID`.
6. **Manage members** — `/organization/members`: invite, role change, suspend, remove, ownership transfer (owner).
7. **Org settings** — `/organization/settings`. Changes emit `org.config_changed`.
8. **Activity / audit** — `/organization/activity` (excludes `auth.*` / `user.*`). Full audit search/export via `GET /api/v1/audit-logs`.

## Assessment loop

9. **Create a project** — `/projects`. Projects group assets, scans, findings, and reports.
10. **Inventory assets** — `/projects/:projectId/assets`. Types include website, domain, public_ip, server, and others (see [scope](./scope.md)). Hierarchy and peer links are supported. Only `active` assets can be scanned.
11. **Run a scan** — `/projects/:projectId/assets/:assetId/scans`. Profiles: quick, full, custom. Execution is inline in development by default, otherwise Celery.
12. **Review findings** — asset and project findings pages. Statuses: open, in_review, resolved, false_positive, accepted.
13. **See risk** — dashboard and risk APIs. Score is **0–100, higher = more secure** (`100 - total_risk_points`). Not AI-generated.
14. **Dashboard** — `/dashboard`. Org security intelligence, including activity feed and monitoring server cards.
15. **Generate PDF reports** — org, project, and asset report pages. Types: executive, technical, weekly, monthly.
16. **Ask AI** — `/ai-assistant` and asset “Ask AI”. Needs `ai:use` and `OPENAI_API_KEY` for live answers. Context is structured facts, not raw SQL.

## Monitoring (server assets)

17. **Enroll an agent** on `server`, `windows_server`, or `docker_host` (`/projects/:projectId/assets/:assetId/monitoring`).
18. **Heartbeat and alerts** — agent posts metrics every 30s. Delayed at 1 minute (display). Offline at 5 minutes plus a `SERVER_OFFLINE` finding. Monitoring **alerts** are separate from scan **findings**.

## Out of scope as use cases (not built)

- Issue API keys and call the API as a machine user
- Configure webhooks or in-app notification delivery
- Prove ownership of a third-party IP before scanning
- Restore a deleted organization
- Bill a tenant
