# Test inventory

CI runs `scripts/ci/check-test-inventory.sh` to ensure every file here exists and every `backend/tests/test_*.py` is documented (no silent drift vs the traceability matrix).

## `backend/tests/`

| File | Area |
|------|------|
| `test_auth.py` | Register/login/refresh/reset paths |
| `test_jwt_security.py` | Expired/invalid/malformed JWT, refresh invalidation, session mismatch |
| `test_rbac.py` | Viewer/manager/analyst/admin/owner permission boundaries |
| `test_organizations.py` | Org CRUD |
| `test_organization_activity.py` | Activity feed |
| `test_members.py` | Members |
| `test_member_lifecycle.py` | Member lifecycle |
| `test_invitations.py` | Invites |
| `test_projects.py` | Projects |
| `test_org_isolation.py` | Cross-tenant isolation |
| `test_assets.py` | Asset CRUD |
| `test_asset_bulk_actions.py` | Bulk actions |
| `test_asset_card_fields.py` | Card fields |
| `test_asset_findings.py` | Asset findings |
| `test_asset_notes.py` | Notes |
| `test_asset_overview.py` | Overview |
| `test_asset_relationships.py` | Relationships / hierarchy |
| `test_asset_reports.py` | Asset-scoped reports |
| `test_asset_risk_history.py` | Risk history |
| `test_asset_scan_schedules.py` | Scan schedules |
| `test_asset_tags_search.py` | Tags / search |
| `test_asset_timeline.py` | Timeline |
| `test_asset_verification.py` | Ownership challenge/verify, scan gate |
| `test_scans.py` | Scans |
| `test_scan_history.py` | Scan history |
| `test_product_pipeline.py` | API E2E pipeline (mocked externals) |
| `test_risk_engine.py` | Scoring engine |
| `test_dashboard.py` | Dashboard |
| `test_project_reports.py` | Project reports |
| `test_reports_rbac.py` | Report RBAC |
| `test_report_storage.py` | Report file storage |
| `test_backup_restore.py` | Backup/restore Docker integration |
| `test_production_config.py` | Production startup validator |
| `test_production_security_boundary.py` | Production public-edge blocks |
| `test_monitoring.py` | Agent/metrics/alerts |
| `test_audit_logs.py` | Audit API, export, integrity |

## `backend/app/*/tests.py`

auth, users, members, organizations, projects, assets, scans, findings, reports, risk, audit, monitoring, plus `core/scan_engine/tests.py`.

## Audit-specific cautions (already fixed in suite)

- Do not `db.refresh(scan)` after a mocked orchestrator that completed in memory — refresh can overwrite status from DB.
- Hash tests must use stored `created_at` precision consistently with the canonical hash payload.
