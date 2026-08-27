# Audit Event Catalog

Source: `backend/app/audit/events.py` and feature-specific `*/events.py` files.

**Canonical form:** `{domain}.{action}` (e.g. `asset.create`). Do not use `ASSET_CREATED`, `asset.created`, or `asset_create` as the documented primary spelling.

Input aliases such as `ASSET_CREATED` are accepted and normalized via `backend/app/events/names.py`. Naming rules: [glossary.md](../glossary.md).

## Authentication

| Event | Description |
|-------|-------------|
| `auth.register` | User registered |
| `auth.login` | User login success |
| `auth.login_failed` | User login failure |
| `auth.account_locked` | Account locked after failed attempts |
| `auth.account_disabled` | Account disabled (member suspended) |
| `auth.logout` | User logout |
| `auth.refresh` | Token refreshed (existing; not shown on the activity feed) |
| `auth.password_change` | Password changed |
| `auth.password_reset_request` | Password reset requested |
| `auth.password_reset` | Password reset completed |
| `auth.email_verified` | Email verified via OTP |
| `auth.session_revoked` | Single session revoked |
| `auth.sessions_revoked_others` | Other sessions revoked |
| `auth.sessions_revoked_all` | All sessions revoked |

## User

| Event | Description |
|-------|-------------|
| `user.profile_update` | Profile fields updated |

## Organization & members

| Event | Description |
|-------|-------------|
| `org.create` | Organization created |
| `org.update` | Organization updated |
| `org.config_changed` | System configuration changed (org settings) |
| `org.delete` | Organization deleted |
| `org.archive` | Organization archived |
| `org.restore` | Organization restored |
| `org.risk_score_changed` | Organization risk score recalculated |
| `org.member_invite` | Member invited |
| `org.member_invite_revoke` | Invite revoked |
| `org.member_accept` | Invite accepted |
| `org.member_update` | Role changed / member status updated |
| `org.member_remove` | Member removed |
| `org.ownership_transfer` | Ownership transferred |

## Projects

| Event | Description |
|-------|-------------|
| `project.create` | Project created |
| `project.update` | Project updated |
| `project.delete` | Project deleted |

## Assets

| Event | Description |
|-------|-------------|
| `asset.create` | Asset created |
| `asset.update` | Asset updated |
| `asset.delete` | Asset deleted |
| `asset.archive` | Asset archived |
| `asset.restore` | Asset restored |

## Scans

| Event | Description |
|-------|-------------|
| `scan.create` | Scan created |
| `scan.run` | Scan queued / started from the API |
| `scan.started` | Scan execution started |
| `scan.completed` | Scan completed |
| `scan.failed` | Scan failed |
| `scan.cancel` | Scan cancelled |
| `scan.plugin_failed` | Plugin failed |

## Findings

| Event | Description |
|-------|-------------|
| `finding.update` | Finding fields/status updated |
| `finding.review` | Finding review action |

## Reports

| Event | Description |
|-------|-------------|
| `report.create` | Report record created |
| `report.update` | Report metadata updated |
| `report.generate` | Report generated |
| `report.regenerate` | Report re-generated |
| `report.download` | Report downloaded |
| `report.delete` | Report deleted |

## AI

Emitted from `AIService.chat` (`backend/app/services/ai/service.py`). **`ai.chat` is only the fallback** for `capability=general`. Other capabilities use the rows below. A new conversation also writes `ai.conversation_started` **in addition to** the capability event.

| Event | Description | Emitted when |
|-------|-------------|--------------|
| `ai.conversation_started` | Conversation started | First turn (`conversation_id` omitted) |
| `ai.explanation_requested` | AI explanation requested | `explain_finding` |
| `ai.remediation_generated` | AI remediation generated | `remediation` |
| `ai.summary_generated` | AI summary generated | `executive_summary`, `technical_summary`, `asset_summary`, `organization_overview`, `compare_scans`, `explain_risk_score` |
| `ai.chat` | General AI assistant turn | `general` (default) |

Full mapping: [docs/ai/README.md](../ai/README.md#audit-events).

## Monitoring

| Event | Description |
|-------|-------------|
| `monitoring.enroll` | Short-lived install/enrollment token issued |
| `monitoring.register` | Agent exchanged enrollment token for a per-server credential |
| `monitoring.revoke` | Agent token revoked |
| `monitoring.alert_opened` | New monitoring alert opened (not every refresh) |

## Administrative

| Event | Description |
|-------|-------------|
| `org.member_update` | User permission / role changed |
| `org.config_changed` | System configuration changed |
| `admin.api_key_created` | API key created (**reserved** — no key API yet) |
| `admin.api_key_revoked` | API key revoked (**reserved** — no key API yet) |

## Feature-specific aliases

Some modules re-export or extend `AuditAction`:

- `backend/app/reports/events.py` — `ReportAuditAction`
- `backend/app/scans/events.py` — `ScanAuditAction`
- `backend/app/findings/events.py` — `FindingAuditAction`
- `backend/app/assets/events.py` — `AssetAuditAction`
- `backend/app/monitoring/events.py` — `MonitoringAuditAction`

Use the canonical string values above in queries and dashboards.
