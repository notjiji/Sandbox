# Tables (as implemented)

`__tablename__` values from SQLAlchemy models. Tests that only `assert __tablename__` are not listed as product tables.

## Identity and tenancy

| Table | Role |
|-------|------|
| `users` | Global account: email, `hashed_password`, names, `is_verified`, `is_active`, `is_superuser`, `last_login` |
| `refresh_tokens` | Hashed refresh, expiry, revoke, rotation `replaced_by_id` |
| `password_reset_tokens` | Hashed reset tokens |
| `email_verification_otps` | Hashed OTP, attempts |
| `organizations` | Tenant: slug, settings JSONB, `is_active`, `deleted_at` |
| `organization_members` | Unique (org, user); role enum; status enum |
| `organization_invites` | Email invite, hashed token, status, expiry |

## Assets and scans

| Table | Role |
|-------|------|
| `projects` | Unique (org, slug); `is_active` |
| `assets` | Type/status/environment/criticality; `parent_id`; `notes`; soft delete |
| `asset_metadata` | Key/value per asset |
| `asset_tags` | Tags |
| `asset_links` | Peer links (`depends_on`, `hosts`, …) |
| `asset_saved_filters` | Per user+project named filter JSON |
| `asset_scan_schedules` | Preset + scan type + next_run |
| `scans` | Type, selected_plugins JSON, lifecycle timestamps |
| `scan_plugin_runs` | Per-plugin status for a scan |
| `findings` | Normalized issues; `source` scan or monitoring |

Asset notes are a **column** on `assets` (migration 028), not a `notes` table.

## Risk and reports

| Table | Role |
|-------|------|
| `recommendations` | Global recommendation text by code |
| `risk_rules` | Unique (plugin, finding_code); score, severity, condition JSON |
| `project_risk_metrics` | Snapshot per project |
| `asset_risk` | Snapshot per asset (latest rows used by engine) |
| `organization_risk` | One row per org (`overall_score`) |
| `organization_risk_history` | Time series |
| `reports` | PDF metadata, type, status, optional asset/scan |

## Audit

| Column | Notes |
|--------|-------|
| `action` | Dot-separated name |
| `resource_type` / `resource_id` | DB names. API aliases: entity_type / entity_id |
| `severity` | info / warning / error / critical (migration 044) |
| `details` | JSONB |
| `prev_hash` / `entry_hash` | SHA-256 hex, nullable for pre-045 rows (migration 045). Chain is per organization; verify skips NULL hashes. |
| `ip_address`, `user_agent` | Request metadata when provided |

## AI

`ai_conversations`, `ai_messages`, `ai_prompts`, `ai_usage`.

## Monitoring

`monitoring_agents` (unique `asset_id`; enrollment + credential hashes; status including `delayed`).  
`monitoring_snapshots` (latest heartbeat document).  
`monitoring_metrics` (time series).  
`monitoring_alerts` (open/resolved) — **not** the `findings` table.

## Naming traps

- Do not document `entity_type` as a physical column.
- Do not document a separate findings table for monitoring alerts.
- Do not document API-key tables — they do not exist.
