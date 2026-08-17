# Functional requirements (as built)

Requirements below describe **current behavior**. They are not a backlog.

## Registration and login

- Users register with email, password, name. Password is hashed (not stored plaintext).
- Email verification uses a hashed OTP (default 15 minutes, 5 attempts).
- Login issues a JWT access token (default 15 minutes, HS256) and a hashed refresh token (default 30 days).
- Failed logins count toward lockout (default 5 attempts / 15 minute window / 15 minute lock).
- Refresh rotates tokens. Logout and session revoke are supported. `X-Session-ID` identifies the session.
- Auth routes use `RATE_LIMIT_AUTH` (default `10/minute`).
- Deep-dive: [docs/auth/README.md](../auth/README.md).

## Organizations

- A user can create an organization (becomes owner) and belong to many.
- Org-scoped APIs require `Authorization: Bearer` and `X-Organization-ID`.
- Update settings; archive/delete sets `is_active=false` and may set `deleted_at`. There is **no** restore endpoint.
- Activity timeline is org-scoped and omits `auth.*` / `user.*`.
- Deep-dive: [docs/organizations/README.md](../organizations/README.md).

## Projects

- Projects belong to one organization (`organization_id` + unique slug per org).
- They contain assets, scans, findings, and reports.
- Projects can be archived (`is_active=false`) and restored.

## Assets

- Assets belong to a project and copy `organization_id` for isolation.
- Types, parent rules, environment, criticality, owner, tags, metadata, notes, saved filters, and peer `asset_links` are implemented.
- Only `status=active` assets can be scanned (`validate_asset_scannable`).
- Soft delete uses `deleted_at` / `status=deleted`.

## Scanning

- Create a scan against one asset; profiles **quick**, **full**, **custom**.
- Full profile plugins: http_headers, fingerprint, tls, dns, whois, ports, robots, security_txt, cookies, cve.
- Orchestrator: `backend/app/core/scan_engine/`. Adapter translates the asset to plugin targets.
- Plugin failures are isolated (`scan.plugin_failed`); they do not always fail the whole scan.
- `SCAN_RUN_INLINE` defaults to true in `development`, false otherwise. Celery runs `app.jobs.scans`.
- Schedules: `asset_scan_schedules` with presets; beat checks every minute.
- Nmap (`-sV`) is **optional**: used by the ports plugin when `nmap` is on PATH; otherwise the plugin still runs without it.
- There is **no** third-party authorization gate.
- Deep-dive: [docs/scan-engine.md](../scan-engine.md), [docs/scans/README.md](../scans/README.md), [docs/plugins/README.md](../plugins/README.md).

## Findings

- Rows on `findings` with severity, status, plugin, codes, evidence, optional CVE/CWE/CVSS.
- Source is typically scan; monitoring can also write findings (for example `SERVER_OFFLINE`).
- Monitoring **alerts** live in `monitoring_alerts`, not in `findings`.
- Deep-dive: [docs/findings/README.md](../findings/README.md).

## Risk scoring

- After scans, `RiskEngine` applies `risk_rules` and severity points: info 0, low 5, medium 15, high 30, critical 50.
- `security_score = max(0, 100 - total_risk_points)`. **Higher is more secure.**
- Grades from `backend/app/core/risk_engine/scoring.py`: A+ ≥ 95, A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, else F.
- Snapshots: `asset_risk`, `project_risk_metrics`, `organization_risk`, `organization_risk_history`.
- Risk is **not** computed by the AI assistant.
- Deep-dive: [docs/risk/README.md](../risk/README.md) (letter-grade table there omits A+; this page matches the code).

## AI assistant

- Permission `ai:use` (not viewer). API: `/api/v1/organizations/ai`.
- Chat persists `ai_conversations` / `ai_messages`; usage in `ai_usage`.
- Context builders pass structured org/asset/finding facts. The model must not invent vulnerabilities.
- Live calls need `OPENAI_API_KEY`. Empty key: reports use offline templates; chat degrades.
- Audit: `ai.conversation_started` on first message of a conversation; then `ai.chat`, `ai.explanation_requested`, `ai.remediation_generated`, or `ai.summary_generated` by capability. The older `docs/ai/README.md` line that every chat is `ai.chat` is incomplete.
- Deep-dive: [docs/ai/README.md](../ai/README.md).

## Dashboard

- `/dashboard` and `GET /api/v1/organizations/current/dashboard`.
- Includes risk summary, findings breakdown, activity feed, monitoring server cards.
- Deep-dive: [docs/dashboard/README.md](../dashboard/README.md).

## Reports

- Types: executive, technical, weekly, monthly. Status: draft → generating → ready | failed.
- PDF stored with `file_url` / `file_size`. Generation can run inline (`REPORT_RUN_INLINE`) or via Celery.
- Deep-dive: [docs/reports/README.md](../reports/README.md).

## Audit logs

- Meaningful events only (not every HTTP request). Canonical names are dot-separated (`asset.create`).
- Table `audit_logs`: `resource_type` / `resource_id` in DB; API also exposes `entity_type` / `entity_id`.
- Severity: info, warning, error, critical.
- Per-org SHA-256 hash chain; Postgres trigger blocks UPDATE/DELETE.
- APIs: `GET /api/v1/audit-logs`, `/{id}`, `/export?format=csv|pdf`, `/integrity`, also under `/organizations/current/audit-logs`.
- Permission: `org:read`. SIEM: `AUDIT_SIEM_SINK` default `none`.
- Deep-dive: [docs/audit/README.md](../audit/README.md), [event-catalog](../audit/event-catalog.md).

## Monitoring

- Enroll on server-like assets; heartbeat 30s; delayed 60s; offline 300s.
- Agent is read-only (see `agent/SECURITY.md` in the repo if present).
- Deep-dive: [docs/monitoring/README.md](../monitoring/README.md).
