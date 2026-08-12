# Audit Event Catalog

Source: `backend/app/audit/events.py` and feature-specific `*/events.py` files.

## Authentication

| Event | Description |
|-------|-------------|
| `auth.register` | New account created |
| `auth.login` | Successful login |
| `auth.login_failed` | Failed login attempt |
| `auth.account_locked` | Account locked after failed attempts |
| `auth.logout` | User logged out |
| `auth.refresh` | Token refreshed |
| `auth.password_change` | Password changed while authenticated |
| `auth.password_reset_request` | Reset email requested |
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
| `org.update` | Organization settings/profile updated |
| `org.delete` | Organization deleted/archived |
| `org.risk_score_changed` | Organization risk score recalculated |
| `org.member_invite` | Member invited |
| `org.member_invite_revoke` | Invite revoked |
| `org.member_accept` | Invite accepted |
| `org.member_update` | Member role/status updated |
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

## Scans

| Event | Description |
|-------|-------------|
| `scan.create` | Scan record created |
| `scan.run` | Scan execution started/completed |
| `scan.cancel` | Scan cancelled |

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
| `report.generate` | Report generation started/completed |
| `report.regenerate` | Report re-generated |
| `report.download` | PDF downloaded (authenticated) |
| `report.delete` | Report deleted |

## AI

| Event | Description |
|-------|-------------|
| `ai.chat` | AI assistant message exchanged |

## Monitoring

| Event | Description |
|-------|-------------|
| `monitoring.enroll` | Short-lived install/enrollment token issued |
| `monitoring.register` | Agent exchanged enrollment token for a per-server credential |
| `monitoring.revoke` | Agent token revoked |
| `monitoring.alert_opened` | New monitoring alert opened (not every refresh) |

## Feature-specific aliases

Some modules re-export or extend `AuditAction`:

- `backend/app/reports/events.py` — `ReportAuditAction`
- `backend/app/scans/events.py` — `ScanAuditAction`
- `backend/app/findings/events.py` — `FindingAuditAction`
- `backend/app/assets/events.py` — `AssetAuditAction`
- `backend/app/monitoring/events.py` — `MonitoringAuditAction`

Use the canonical string values above in queries and dashboards.
