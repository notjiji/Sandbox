# Functional Requirements

**Product:** Sandbox — Security Intelligence Platform  
**Release:** V1 (as built in this repository)  
**Status:** Source of truth for *what the product must do today*  
**Related:** [Definition](./definition.md) · [Scope](./scope.md) · [Users](./users.md) · [Use cases](./use-cases.md) · [Non-functional](./non-functional-requirements.md)

This document states **functional requirements**, not a backlog. Every `FR-*` below is implemented. Stubs and Future capabilities are listed at the end so they are not treated as requirements.

## How to read this document

| Convention | Meaning |
|------------|---------|
| **ID** | Stable identifier (`FR-<AREA>-<nn>`). Do not reuse an ID for a different behavior. |
| **Shall** | Mandatory V1 behavior. Testable from UI, API, or both. |
| **Actor** | Role or system that exercises the requirement. Roles: `owner`, `admin`, `security_analyst`, `manager`, `viewer`. |
| **Notes** | Defaults, constraints, or pointers. Not extra requirements. |

Org-scoped APIs require `Authorization: Bearer` and `X-Organization-ID` unless a requirement says otherwise.

Capability map: [definition — MVP vs Future](./definition.md). Permission matrix: [RBAC](../rbac/roles-and-permissions.md).

---

## 1. Authentication

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-AUTH-01** | The system shall allow a person to register an account with email, password, and name. | Unauthenticated user | Optional invite token on register. |
| **FR-AUTH-02** | The system shall store passwords as hashes, never as plaintext. | System | Argon2, bcrypt fallback. |
| **FR-AUTH-03** | The system shall require email verification with a hashed one-time code before full access. | User | Default OTP: 15 minutes, 5 attempts. |
| **FR-AUTH-04** | The system shall allow the user to request a new verification code. | User | Rate-limited with other auth routes. |
| **FR-AUTH-05** | The system shall authenticate a verified user and issue a short-lived JWT access token and a hashed refresh token. | User | Access default 15 minutes, HS256. Refresh default 30 days. |
| **FR-AUTH-06** | The system shall rotate tokens on refresh and bind requests to a revocable session (`X-Session-ID`). | User | |
| **FR-AUTH-07** | The system shall allow logout and explicit session revoke. | Authenticated user | |
| **FR-AUTH-08** | The system shall allow password reset via email token and password change while authenticated. | User | Reset token expiry: `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` (default 1). |
| **FR-AUTH-09** | The system shall lock an account after repeated failed logins within a window. | System | Default: 5 failures / 15 minute window / 15 minute lock. |
| **FR-AUTH-10** | The system shall rate-limit authentication endpoints separately from general API traffic. | System | `RATE_LIMIT_AUTH` default `10/minute`. |

Deep-dive: [auth](../auth/README.md).

---

## 2. User profile

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-USER-01** | The system shall let an authenticated user view and update their profile. | User | Global account, not tenant-specific. |
| **FR-USER-02** | The system shall allow a user to belong to zero or more organizations, each with its own role. | User | After login, org is selected unless the user has exactly one. |

`users.is_superuser` exists in the database. It is **not** a product role in the UI (not a V1 requirement).

---

## 3. Organizations

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-ORG-01** | The system shall allow an authenticated user to create an organization and become its owner. | User | |
| **FR-ORG-02** | The system shall isolate all tenant data by `organization_id`. Cross-organization reads and writes shall be rejected. | System | Membership must be active. |
| **FR-ORG-03** | The system shall require `X-Organization-ID` on organization-scoped APIs and reject requests that omit it. | System | Auth routes remain user-scoped. |
| **FR-ORG-04** | The system shall allow authorized members to update organization profile, settings, and branding. | `owner`, `admin` | Settings JSON includes language, branding, notification flags, security flags. Logo: `logo_url`. |
| **FR-ORG-05** | The system shall allow the owner to archive or soft-delete the organization (`is_active=false`). | `owner` | **No restore** in V1. |
| **FR-ORG-06** | The system shall expose an organization activity timeline that omits `auth.*` and `user.*` events. | Members with `org:read` | Distinct from full audit search. |

Deep-dive: [organizations](../organizations/README.md).

---

## 4. Members and invitations

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-MEM-01** | The system shall allow owners and admins to invite a person by email with a chosen organization role. | `owner`, `admin` | |
| **FR-MEM-02** | The system shall expire unused invitations after the configured number of days and allow resend or revoke. | `owner`, `admin` | |
| **FR-MEM-03** | The system shall allow the invited person to accept an invitation and join with the invited role. | Invitee | |
| **FR-MEM-04** | The system shall allow owners and admins to change a member’s role. | `owner`, `admin` | Takes effect on the next authorized request after token refresh. |
| **FR-MEM-05** | The system shall allow owners and admins to suspend, reactivate, or remove a member. The owner shall not be suspendable. | `owner`, `admin` | |
| **FR-MEM-06** | The system shall allow only the owner to transfer organization ownership to another active member. | `owner` | |
| **FR-MEM-07** | The system shall list organization members to roles that have `member:read`. Viewers shall not list members. | `owner`, `admin`, `security_analyst`, `manager` | Viewer has no `member:read`. |

---

## 5. Role-based access

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-RBAC-01** | The system shall enforce one of five organization roles: `owner`, `admin`, `security_analyst`, `manager`, `viewer`. | System | Source: `backend/app/core/permissions.py`. |
| **FR-RBAC-02** | The system shall grant the owner all permissions, including `org:delete` and ownership transfer. | `owner` | `org:billing` exists on the role; there is **no** billing product. |
| **FR-RBAC-03** | The system shall grant admin all permissions except organization delete, billing, and ownership transfer. | `admin` | |
| **FR-RBAC-04** | The system shall allow `security_analyst` to create/update projects and assets, run and cancel scans, review findings, manage monitoring agents, and generate or delete reports — but not delete the organization or manage members. | `security_analyst` | No `asset:delete` / `project:delete` / member mutations. |
| **FR-RBAC-05** | The system shall allow `manager` to read posture, generate reports, and use AI, and shall prevent managers from running scans, mutating assets, or managing agents. | `manager` | |
| **FR-RBAC-06** | The system shall allow `viewer` read-only access to dashboard, assets, scans, findings, reports, and monitoring, and shall deny AI use, member listing, and all mutations. | `viewer` | |

---

## 6. Projects

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-PROJ-01** | The system shall allow authorized members to create a project that belongs to exactly one organization, with a slug unique inside that organization. | `owner`, `admin`, `security_analyst` | |
| **FR-PROJ-02** | The system shall use a project as the container for assets, scans, findings, and reports. | System | |
| **FR-PROJ-03** | The system shall allow authorized members to update project metadata. | `owner`, `admin`, `security_analyst` | |
| **FR-PROJ-04** | The system shall allow members with `project:update` to archive a project (`is_active=false`) and restore it. | `owner`, `admin`, `security_analyst` | Archive is reversible. Hard delete uses `project:delete` (owner, admin). |

---

## 7. Asset management

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-AST-01** | The system shall store each asset in one project and copy `organization_id` for isolation. | System | |
| **FR-AST-02** | The system shall support these asset types: website, domain, public_ip, server, windows_server, docker_host, cloud_account, kubernetes_cluster, api_endpoint, mobile_application, git_repository, email_domain, s3_bucket, azure_subscription. | Analyst / admin | Inventory does not imply a dedicated scanner for every type. |
| **FR-AST-03** | The system shall enforce parent/child type rules (for example a server may hang off a public IP; some types are root-only). | System | `backend/app/assets/enums.py`. |
| **FR-AST-04** | The system shall allow peer links between assets (`depends_on`, `hosts`, `runs_on`, `exposes`, `related`). | Analyst / admin | |
| **FR-AST-05** | The system shall record environment (`production`, `staging`, `development`, `testing`) and criticality (`critical`, `high`, `medium`, `low`) on an asset. | Analyst / admin | |
| **FR-AST-06** | The system shall support tags, metadata, notes, saved filters, bulk actions, and an asset timeline. | Analyst / admin | |
| **FR-AST-07** | The system shall allow scan of an asset only when `status=active`. | System | `validate_asset_scannable`. |
| **FR-AST-08** | The system shall soft-delete assets (`deleted_at`, `status=deleted`). | Roles with `asset:delete` | |
| **FR-AST-09** | The system shall **not** require third-party IP-ownership proof or an allowlist before scanning an in-tenant active asset. | System | Product is for infrastructure the org already manages. |

---

## 8. Scanning

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-SCAN-01** | The system shall create a scan against exactly one asset. | Roles with `scan:create` + `scan:run` | |
| **FR-SCAN-02** | The system shall offer three profiles: **quick**, **full**, and **custom**. | Analyst | Quick: http_headers, tls, dns, cookies. Full: those plus fingerprint, whois, ports, robots, security_txt, cve. Custom: caller-selected plugins (at least one). |
| **FR-SCAN-03** | The system shall run plugins through the scan orchestrator, translating the asset into plugin targets. | System | `backend/app/core/scan_engine/`. |
| **FR-SCAN-04** | The system shall isolate plugin failures: one plugin failing shall not always fail the whole scan, and the failure shall be recorded (`scan.plugin_failed`). | System | |
| **FR-SCAN-05** | The system shall move a scan through `pending` → `queued` → `running` → `completed` \| `failed` \| `cancelled`. | System | |
| **FR-SCAN-06** | The system shall allow an authorized user to cancel a running scan. | Roles with `scan:cancel` | |
| **FR-SCAN-07** | The system shall persist per-plugin runs (`scan_plugin_runs`) and scan history on the asset. | System | |
| **FR-SCAN-08** | The system shall execute scans inline when `SCAN_RUN_INLINE` is true (development default) and via Celery otherwise. | System | |
| **FR-SCAN-09** | The system shall support recurring asset scan schedules with presets, evaluated at least once per minute by the scheduler. | Analyst | Celery beat `check_due_schedules`. |

Deep-dive: [scans](../scans/README.md), [scan engine](../scan-engine.md).

---

## 9. HTTP scanning

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-HTTP-01** | The system shall inspect HTTP security headers (including CSP and HSTS) and emit findings for missing or weak headers. | Scan engine | Plugin `http_headers`. |
| **FR-HTTP-02** | The system shall inspect cookie flags and policies and emit findings. | Scan engine | Plugin `cookies`. |
| **FR-HTTP-03** | The system shall fingerprint technologies on HTTP assets and emit findings where rules match. | Scan engine | Plugin `fingerprint`. On **full** profile, not quick. |
| **FR-HTTP-04** | The system shall fetch `robots.txt` and `security.txt` and emit findings for missing or sensitive content. | Scan engine | Plugins `robots`, `security_txt`. Full profile. |

---

## 10. SSL / TLS

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-TLS-01** | The system shall inspect TLS certificates (validity, chain, related issues) and emit findings. | Scan engine | Plugin `ssl`. |
| **FR-TLS-02** | The system shall inspect TLS protocol configuration and emit findings for insecure protocols or ciphers. | Scan engine | Plugin `tls`. Included on **quick** and **full**. |

---

## 11. DNS

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-DNS-01** | The system shall collect DNS records for a target and emit findings for misconfigurations defined in the DNS rule catalog. | Scan engine | Plugin `dns`. Quick and full. |

---

## 12. WHOIS

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-WHOIS-01** | The system shall collect domain registration (WHOIS) data and emit findings per WHOIS rules. | Scan engine | Plugin `whois`. Full profile. |

---

## 13. Port scanning

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-PORT-01** | The system shall detect open ports on a scannable target and emit findings per port rules. | Scan engine | Plugin `ports`. Full profile. |
| **FR-PORT-02** | The system shall use Nmap service detection (`-sV`) when `nmap` is on PATH, and shall still complete the ports plugin when Nmap is absent. | System | Nmap is optional, not a hard dependency. |

---

## 14. Findings

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-FND-01** | The system shall persist a normalized finding with title, stable `finding_code`, severity, status, plugin, evidence, recommendation, and links to asset, project, and (when from a scan) scan. | System | Optional CVE / CWE / CVSS fields may be present; they do not constitute a CVE intelligence product. |
| **FR-FND-02** | The system shall use severities `critical`, `high`, `medium`, `low`, `info`. | System | |
| **FR-FND-03** | The system shall use statuses `open`, `in_review`, `resolved`, `false_positive`, `accepted`. | Analyst | Roles with `finding:review` / `finding:update`. |
| **FR-FND-04** | The system shall allow listing and filtering findings at project and asset scope. | Roles with `finding:read` | |
| **FR-FND-05** | The system shall accept findings from scans (`source=scan`) and from monitoring (`source=monitoring`, for example `SERVER_OFFLINE` or host security conditions). | System | Operational CPU/disk events stay in `monitoring_alerts`, not in `findings`. |
| **FR-FND-06** | The system shall not duplicate findings into report tables; reports shall read current in-scope findings at generation time. | System | |

Deep-dive: [findings](../findings/README.md).

---

## 15. Risk engine

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-RSK-01** | The system shall compute a deterministic security score from open findings using fixed severity points: info 0, low 5, medium 15, high 30, critical 50. | System | `RiskEngine`. Resolved / false-positive / accepted findings do not count as open risk. |
| **FR-RSK-02** | The system shall set `security_score = max(0, 100 - total_risk_points)`. Higher shall mean more secure. | System | |
| **FR-RSK-03** | The system shall map scores to grades: A+ ≥ 95, A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, else F. | System | `backend/app/core/risk_engine/scoring.py`. |
| **FR-RSK-04** | The system shall store scores at asset, project, and organization level, plus organization history for trends. | System | `asset_risk`, `project_risk_metrics`, `organization_risk`, `organization_risk_history`. |
| **FR-RSK-05** | The system shall recalculate risk after scan completion. Finding status changes shall be reflected on the next calculation. | System | |
| **FR-RSK-06** | The system shall **not** use the AI assistant to compute or override the security score. | System | AI may explain stored scores; it must not invent them. |

Deep-dive: [risk](../risk/README.md), [scoring model](../risk/scoring-model.md).

---

## 16. AI assistant

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-AI-01** | The system shall provide an organization-scoped chat assistant to members with `ai:use`. Viewers shall be denied. | `owner`, `admin`, `security_analyst`, `manager` | `/api/v1/organizations/ai`. |
| **FR-AI-02** | The system shall persist conversations, messages, and usage for the organization. | System | |
| **FR-AI-03** | The system shall send the model structured facts (scores, counts, top issues, selected asset) and shall instruct it not to invent vulnerabilities. | System | No raw SQL or full table dumps. |
| **FR-AI-04** | The system shall call a live model only when `OPENAI_API_KEY` is set; otherwise chat shall degrade and report summaries shall use an offline template. | System | |
| **FR-AI-05** | The system shall audit AI use: `ai.conversation_started` on the first message, then `ai.chat`, `ai.explanation_requested`, `ai.remediation_generated`, or `ai.summary_generated` by capability. | System | |

Deep-dive: [AI](../ai/README.md).

---

## 17. Dashboard

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-DASH-01** | The system shall show an organization Security Intelligence dashboard sourced from live APIs, not hardcoded scores. | All roles (`dashboard:view`) | `/dashboard`, `GET /api/v1/organizations/current/dashboard`. |
| **FR-DASH-02** | The dashboard shall include current org score and grade, change vs previous, findings by severity, asset overview, top risky assets, upcoming scheduled scans, enrolled server cards, and a compact activity feed. | Viewer+ | |
| **FR-DASH-03** | The dashboard shall deep-link findings (including `?severity=critical`) and shall hide scan-run actions from roles without `scan:run`. | UI | |
| **FR-DASH-04** | The dashboard shall offer generate-report entry points only to roles with `report:generate`. | Manager+ | |

Deep-dive: [dashboard](../dashboard/README.md).

---

## 18. Reports

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-RPT-01** | The system shall generate PDF reports of types `executive`, `technical`, `weekly`, and `monthly`. | Roles with `report:generate` | Weekly/monthly share the executive template. |
| **FR-RPT-02** | The system shall move a report through `draft` → `generating` → `ready` \| `failed`. | System | Inline when `REPORT_RUN_INLINE`, else Celery. |
| **FR-RPT-03** | The system shall collect in-scope findings, scores, and branding at generation time and render them to PDF. | System | Org branding (logo, colors, footer, contact) flows into the template. |
| **FR-RPT-04** | The system shall include an AI summary when OpenAI is configured, otherwise an offline template summary. | System | Facts-only prompt; must not invent findings. |
| **FR-RPT-05** | The system shall allow authenticated preview (HTML) and download (PDF) of a ready report. PDFs shall not be served from a public static path. | Roles with `report:read` (all roles) | |
| **FR-RPT-06** | The system shall allow deletion of a report and its files by roles with `report:delete`. Managers and viewers shall not delete. | `owner`, `admin`, `security_analyst` | |
| **FR-RPT-07** | The system shall list reports at organization, project, and asset scope. | Roles with `report:read` | |

Deep-dive: [reports](../reports/README.md).

---

## 19. Server monitoring

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-MON-01** | The system shall allow enrollment of a monitoring agent only on `server`, `windows_server`, and `docker_host` assets. | Roles with `monitoring:manage` | |
| **FR-MON-02** | The system shall issue a one-time enrollment token (`sbe_…`) that expires in 15 minutes. | System | Shown in the install command; not a long-lived secret. |
| **FR-MON-03** | The system shall issue a per-server ingest credential (`sba_…`) to the agent on register and shall never display that credential in the UI. | System | |
| **FR-MON-04** | The system shall accept agent register and ingest with the agent credential only — not a user JWT and not `X-Organization-ID`. | Agent | |
| **FR-MON-05** | The agent shall be read-only: collect host facts over outbound HTTPS, and shall not accept commands, open a shell, or SSH inbound from the platform. | Agent | [agent security](../../agent/SECURITY.md). |
| **FR-MON-06** | The system shall treat heartbeats every 30 seconds as healthy, mark **Delayed** after 60 seconds without a heartbeat, and mark **Offline** after 300 seconds (including a `SERVER_OFFLINE` finding). | System | |
| **FR-MON-07** | The system shall store CPU, RAM, disk, network, and load history and show them on the asset monitoring page and dashboard server cards. | Roles with `monitoring:read` (all roles) | Also process, Docker, firewall, SSH, Fail2Ban, and update facts when reported. |
| **FR-MON-08** | The system shall keep operational alerts (`monitoring_alerts`) separate from security findings, except where a host security condition is explicitly promoted to a finding. | System | |
| **FR-MON-09** | The system shall allow revoke of one server’s credential without affecting other enrolled hosts. | Roles with `monitoring:manage` | |

Deep-dive: [monitoring](../monitoring/README.md).

---

## 20. Audit

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-AUD-01** | The system shall record meaningful domain events (not every HTTP request) with dot-separated action names (for example `asset.create`). | System | Catalog: [event-catalog](../audit/event-catalog.md). |
| **FR-AUD-02** | The system shall store each audit row with organization, actor, resource, severity (`info`, `warning`, `error`, `critical`), details, IP, and user agent. | System | APIs expose `entity_type` / `entity_id` for `resource_*`. |
| **FR-AUD-03** | The system shall make audit rows append-only. PostgreSQL shall reject UPDATE and DELETE on `audit_logs`. | System | Application code never updates or deletes rows. |
| **FR-AUD-04** | The system shall maintain a per-organization SHA-256 hash chain (`prev_hash`, `entry_hash`) and expose an integrity check API. | System | `GET /api/v1/audit-logs/integrity`. Verification skips legacy rows with NULL hashes. |
| **FR-AUD-05** | The system shall allow members with `org:read` to list, get, filter, and export audit logs as CSV or PDF. | Roles with `org:read` | Filters: action, severity, user, asset, date, entity. |
| **FR-AUD-06** | The system shall not fail the business action if audit persist or SIEM export fails. | System | SAVEPOINT / fail-safe; subscribers are independent. |
| **FR-AUD-07** | The system shall not persist secrets (passwords, tokens, API keys) in audit details. | System | |

Deep-dive: [audit](../audit/README.md).

---

## 21. SIEM adapters

| ID | Requirement | Actor | Notes |
|----|-------------|-------|-------|
| **FR-SIEM-01** | The system shall forward persisted audit events to an optional SIEM sink after the row is written. | System | Best-effort; sink outage must not fail the API. |
| **FR-SIEM-02** | The system shall support sinks `none` (default), `syslog`, `splunk`, `elk`, and `sentinel`, selected by `AUDIT_SIEM_SINK`. | Operator | Env-configured; no SIEM UI in V1. |
| **FR-SIEM-03** | The system shall not require a SIEM to use the product. With `AUDIT_SIEM_SINK=none`, audit remains in Postgres only. | Operator | |

---

## Requirement count

| Area | IDs | Count |
|------|-----|------:|
| Authentication | FR-AUTH-01 … 10 | 10 |
| User profile | FR-USER-01 … 02 | 2 |
| Organizations | FR-ORG-01 … 06 | 6 |
| Members | FR-MEM-01 … 07 | 7 |
| RBAC | FR-RBAC-01 … 06 | 6 |
| Projects | FR-PROJ-01 … 04 | 4 |
| Assets | FR-AST-01 … 09 | 9 |
| Scanning | FR-SCAN-01 … 09 | 9 |
| HTTP | FR-HTTP-01 … 04 | 4 |
| SSL/TLS | FR-TLS-01 … 02 | 2 |
| DNS | FR-DNS-01 | 1 |
| WHOIS | FR-WHOIS-01 | 1 |
| Ports | FR-PORT-01 … 02 | 2 |
| Findings | FR-FND-01 … 06 | 6 |
| Risk | FR-RSK-01 … 06 | 6 |
| AI | FR-AI-01 … 05 | 5 |
| Dashboard | FR-DASH-01 … 04 | 4 |
| Reports | FR-RPT-01 … 07 | 7 |
| Monitoring | FR-MON-01 … 09 | 9 |
| Audit | FR-AUD-01 … 07 | 7 |
| SIEM | FR-SIEM-01 … 03 | 3 |
| **Total** | | **110** |

110 is slightly above the 50–100 target because scanners and RBAC are split so each capability in the [definition table](./definition.md) has its own IDs. Do not add speculative requirements for Future rows.

---

## Out of scope (not requirements in V1)

These are **not** functional requirements. Code may exist as a stub.

| Capability | Why it is not a V1 requirement |
|------------|--------------------------------|
| Malware analysis | `plugins/future/malware` is loaded with `enabled=False`. |
| Threat intelligence | No feed, IOC, or reputation product. |
| CVE intelligence | Hint-based OSV lookup on the full profile is not a CVE platform. Do not write FRs for inventory, KEVs, or exploit correlation. |
| Cloud security | `plugins/future/cloud` disabled; cloud types are inventory-only. |
| Kubernetes security | `plugins/future/kubernetes` disabled. |
| Webhooks | Event-bus subscriber not built. |
| Analytics product | Dashboard summaries are V1 (FR-DASH-*). No BI/analytics product. |
| Notifications delivery | Hook logs only; no email/in-app notification center. |
| API keys / machine auth | Catalogued audit names only; not issued. |
| Billing | Permission exists; no billing product. |
| Organization restore | Archive/delete is one-way. |
| Third-party scan authorization | No DNS TXT / IP-ownership proof. |
| Inbound SSH / agent command channel | Explicitly forbidden (FR-MON-05). |

When a Future item ships, add `FR-*` rows here, mark the capability V1 in [definition](./definition.md), and remove it from [roadmap/planned](../roadmap/planned.md).
