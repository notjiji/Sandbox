# Test inventory

## `backend/tests/`

| File | Area |
|------|------|
| `test_auth.py` | Register/login/refresh/reset paths |
| `test_jwt_security.py` | Expired/invalid/malformed JWT, refresh invalidation, session mismatch |
| `test_rbac.py` | Viewer/manager/analyst/admin/owner permission boundaries |
| `test_organizations.py` | Org CRUD |
| `test_organization_activity.py` | Activity feed |
| `test_members.py` / `test_member_lifecycle.py` | Members |
| `test_invitations.py` | Invites |
| `test_projects.py` | Projects |
| `test_org_isolation.py` | Cross-tenant isolation (assets, projects, scans, findings, reports, AI conversations, audit logs, monitoring) |
| `test_assets.py` plus `test_asset_*` | Assets, tags, notes, bulk, timeline, relationships, overview, card fields, findings, reports, schedules, risk history |
| `test_scans.py` / `test_scan_history.py` | Scans |
| `test_product_pipeline.py` | API E2E: user → org → project → asset → **verify** → scan/plugins → findings → risk → AI → report → audit (external HTTP/DNS/TLS/LLM mocked) |
| `test_asset_verification.py` | Ownership challenge/verify, scan gate, invalidation on identity updates |
| `test_risk_engine.py` | Scoring engine |
| `test_dashboard.py` | Dashboard |
| `test_project_reports.py` / `test_asset_reports.py` / `test_reports_rbac.py` / `test_report_storage.py` | Reports |
| `test_monitoring.py` | Agent/metrics/alerts |
| `test_audit_logs.py` | Audit API, export, integrity |

## `backend/app/*/tests.py`

auth, users, members, organizations, projects, assets, scans, findings, reports, risk, audit, monitoring, plus `core/scan_engine/tests.py`.

## Audit-specific cautions (already fixed in suite)

- Do not `db.refresh(scan)` after a mocked orchestrator that completed in memory — refresh can overwrite status from DB.
- Hash tests must use stored `created_at` precision consistently with the canonical hash payload.
