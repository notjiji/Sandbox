# Requirements Traceability Matrix

**Purpose:** Prove that every V1 requirement has an implementation, automated tests (where enforceable), and documentation.

**Sources of truth**

| Artifact | Location |
|----------|----------|
| Functional requirements | [docs/product/functional-requirements.md](../product/functional-requirements.md) |
| Non-functional requirements | [docs/product/non-functional-requirements.md](../product/non-functional-requirements.md) |
| Test inventory | [docs/testing/inventory.md](../testing/inventory.md) |
| Naming conventions | [docs/glossary.md](../glossary.md) |

**How to read**

| Column | Meaning |
|--------|---------|
| **Requirement** | Stable ID + short title (full shall-text lives in the FR/NFR docs). |
| **Implementation** | Primary modules / packages that fulfill the requirement. |
| **Tests** | Primary pytest files. Paths are under `backend/` unless noted. |
| **Documentation** | Product FR row plus deep-dive docs. |
| **Coverage** | `Covered` = automated test asserts the behavior · `Partial` = implemented + docs, thin or indirect tests · `Intent` = documented target, not asserted in CI · `Policy` = enforced by code/config/docs, no dedicated test |

Update this matrix whenever you add, change, or retire an `FR-*` / `NFR-*` ID.

---

## Coverage summary

| Area | IDs | Covered / Partial / Intent+Policy |
|------|-----|-------------------------------------|
| Functional (FR-*) | 110 | See sections below — all have implementation + docs; tests vary by area |
| Non-functional (NFR-*) | 77 | Enforced NFRs map to code; Intent/ops items marked explicitly |
| Frontend e2e | — | **None** in V1 (`package.json` has typecheck/build only) |

End-to-end product path (user → org → project → asset → scan → findings → risk → AI → report → audit): `tests/test_product_pipeline.py`.

---

## 1. Authentication — FR-AUTH

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-AUTH-01** Registration | `app/auth/` (register router/service) | `tests/test_auth.py`, `app/auth/tests.py` | [auth](../auth/README.md), FR-AUTH-01 | Covered |
| **FR-AUTH-02** Password hashing | `app/core/security.py` | `tests/test_auth.py`, `tests/test_jwt_security.py` | [security](../security/README.md), NFR-SEC-01…03 | Covered |
| **FR-AUTH-03** Email OTP verification | `app/auth/` OTP models/services | `tests/test_auth.py` | [auth](../auth/README.md) | Covered |
| **FR-AUTH-04** Resend verification code | `app/auth/` | `tests/test_auth.py` | [auth](../auth/README.md) | Partial |
| **FR-AUTH-05** Login + JWT + refresh | `app/auth/`, `app/core/security.py` | `tests/test_auth.py`, `tests/test_jwt_security.py` | [auth](../auth/README.md), [security/auth](../security/auth.md) | Covered |
| **FR-AUTH-06** Refresh rotation + session | `app/auth/` sessions / refresh | `tests/test_jwt_security.py`, `tests/test_auth.py` | [auth](../auth/README.md) | Covered |
| **FR-AUTH-07** Logout / session revoke | `app/auth/` | `tests/test_auth.py`, `tests/test_jwt_security.py` | [auth](../auth/README.md) | Covered |
| **FR-AUTH-08** Password reset / change | `app/auth/` | `tests/test_auth.py` | [auth](../auth/README.md) | Covered |
| **FR-AUTH-09** Account lockout | `app/auth/` + Redis lockout | Auth services (lockout paths) | [auth](../auth/README.md), NFR-SEC-12 | Partial |
| **FR-AUTH-10** Auth rate limit | SlowAPI + `RATE_LIMIT_AUTH` | Config / middleware (no dedicated load test) | [auth](../auth/README.md), NFR-SEC-13 | Policy |

---

## 2. User profile — FR-USER

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-USER-01** View/update profile | `app/users/` | `tests/test_auth.py`, `app/users/tests.py` | FR-USER-01 | Covered |
| **FR-USER-02** Multi-org membership | `app/users/`, `app/members/`, org switch UI | `tests/test_organizations.py`, `tests/test_members.py` | [organizations](../organizations/README.md) | Covered |

---

## 3. Organizations — FR-ORG

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-ORG-01** Create org (owner) | `app/organizations/` | `tests/test_organizations.py` | [organizations](../organizations/README.md) | Covered |
| **FR-ORG-02** Tenant isolation | Org-scoped repos + membership deps | `tests/test_org_isolation.py` | [security/tenancy](../security/tenancy.md) | Covered |
| **FR-ORG-03** Require `X-Organization-ID` | `require_organization` deps | `tests/test_org_isolation.py`, `tests/test_rbac.py` | [organizations](../organizations/README.md) | Covered |
| **FR-ORG-04** Update settings/branding | `app/organizations/` | `tests/test_organizations.py` | [organizations](../organizations/README.md) | Covered |
| **FR-ORG-05** Soft-delete / archive org | `app/organizations/` | `tests/test_organizations.py` | [organizations](../organizations/README.md) | Partial |
| **FR-ORG-06** Activity timeline | Org activity endpoint | `tests/test_organization_activity.py` | [organizations](../organizations/README.md), [audit](../audit/README.md) | Covered |

---

## 4. Members — FR-MEM

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-MEM-01** Invite by email + role | `app/members/` invites | `tests/test_invitations.py` | [rbac](../rbac/README.md) | Covered |
| **FR-MEM-02** Invite expiry / resend / revoke | `app/members/` | `tests/test_invitations.py` | FR-MEM-02 | Partial |
| **FR-MEM-03** Accept invitation | `app/members/` | `tests/test_invitations.py` | FR-MEM-03 | Covered |
| **FR-MEM-04** Change member role | `app/members/` | `tests/test_members.py`, `tests/test_member_lifecycle.py` | [rbac](../rbac/README.md) | Covered |
| **FR-MEM-05** Suspend / reactivate / remove | `app/members/` | `tests/test_member_lifecycle.py` | FR-MEM-05 | Partial |
| **FR-MEM-06** Ownership transfer | `app/members/` / org service | Member lifecycle (thin) | FR-MEM-06 | Partial |
| **FR-MEM-07** Member list RBAC | `member:read` permission | `tests/test_rbac.py`, `tests/test_members.py` | [rbac/roles-and-permissions](../rbac/roles-and-permissions.md) | Covered |

---

## 5. RBAC — FR-RBAC

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-RBAC-01** Five org roles | `app/core/permissions.py`, `app/members/enums.py` | `tests/test_rbac.py` | [rbac](../rbac/README.md), [glossary](../glossary.md) | Covered |
| **FR-RBAC-02** Owner full perms | Role → permission map | `tests/test_rbac.py` | [rbac/roles-and-permissions](../rbac/roles-and-permissions.md) | Covered |
| **FR-RBAC-03** Admin (no delete/billing/transfer) | Role → permission map | `tests/test_rbac.py` | Same | Covered |
| **FR-RBAC-04** Security analyst bounds | Role → permission map | `tests/test_rbac.py` | Same | Covered |
| **FR-RBAC-05** Manager bounds | Role → permission map | `tests/test_rbac.py`, `tests/test_reports_rbac.py` | Same | Covered |
| **FR-RBAC-06** Viewer read-only | Role → permission map | `tests/test_rbac.py` | Same | Covered |

---

## 6. Projects — FR-PROJ

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-PROJ-01** Create project + unique slug | `app/projects/` | `tests/test_projects.py` | FR-PROJ-01 | Covered |
| **FR-PROJ-02** Project as container | Models FK to `project_id` | `tests/test_product_pipeline.py`, `tests/test_org_isolation.py` | [database/tables](../database/tables.md) | Covered |
| **FR-PROJ-03** Update metadata | `app/projects/` | `tests/test_projects.py` | FR-PROJ-03 | Covered |
| **FR-PROJ-04** Archive / restore / hard delete | `app/projects/` | `tests/test_projects.py` | FR-PROJ-04 | Covered |

---

## 7. Assets — FR-AST

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-AST-01** Asset in project + org_id | `app/assets/` | `tests/test_assets.py`, `tests/test_org_isolation.py` | FR-AST-01 | Covered |
| **FR-AST-02** Asset types | `app/assets/enums.py` | `tests/test_assets.py` | [glossary](../glossary.md) | Covered |
| **FR-AST-03** Parent/child type rules | `app/assets/enums.py` / validators | `tests/test_assets.py`, `tests/test_asset_relationships.py` | FR-AST-03 | Covered |
| **FR-AST-04** Peer links | `asset_links` | `tests/test_asset_relationships.py` | FR-AST-04 | Covered |
| **FR-AST-05** Environment + criticality | Asset model/schemas | `tests/test_assets.py`, `tests/test_asset_card_fields.py` | FR-AST-05 | Covered |
| **FR-AST-06** Tags, notes, filters, bulk, timeline | `app/assets/` services | `tests/test_asset_tags_search.py`, `test_asset_notes.py`, `test_asset_bulk_actions.py`, `test_asset_timeline.py` | FR-AST-06 | Covered |
| **FR-AST-07** Scannable only if active (+ verified for web/domain/IP) | `validate_asset_scannable`, verification gate | `tests/test_asset_verification.py`, `tests/test_scans.py` | [security/scanning](../security/scanning.md) | Covered |
| **FR-AST-08** Soft-delete assets | Asset delete service | `tests/test_assets.py` | FR-AST-08 | Covered |
| **FR-AST-09** Ownership verification (domain/DNS/HTTP/IP) | `app/assets/services/verification_service.py` | `tests/test_asset_verification.py` | FR-AST-09, [security/scanning](../security/scanning.md) | Covered |

---

## 8. Scanning — FR-SCAN

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-SCAN-01** Scan against one asset | `app/scans/` | `tests/test_scans.py`, `tests/test_product_pipeline.py` | [scans](../scans/README.md) | Covered |
| **FR-SCAN-02** Profiles quick / full / custom | `app/scans/profiles.py` | `tests/test_scans.py`, `tests/test_product_pipeline.py` | [scan-engine](../scan-engine.md), [glossary](../glossary.md) | Covered |
| **FR-SCAN-03** Orchestrator + adapter | `app/core/scan_engine/` | `app/core/scan_engine/tests.py`, `tests/test_product_pipeline.py` | [scan-engine](../scan-engine.md), [architecture/plugins](../architecture/plugins.md) | Covered |
| **FR-SCAN-04** Isolated plugin failure | Orchestrator + `scan.plugin_failed` | Scan engine tests, pipeline | [scan-engine](../scan-engine.md) | Covered |
| **FR-SCAN-05** Scan lifecycle statuses | `app/scans/lifecycle.py` | `tests/test_scans.py` | [glossary](../glossary.md) | Covered |
| **FR-SCAN-06** Cancel scan | Scan cancel API | `tests/test_scans.py` | [scans](../scans/README.md) | Covered |
| **FR-SCAN-07** Plugin runs + history | `scan_plugin_runs`, history APIs | `tests/test_scan_history.py`, `tests/test_scans.py` | [scans](../scans/README.md), [dashboard](../dashboard/README.md) | Covered |
| **FR-SCAN-08** Inline vs Celery | `SCAN_RUN_INLINE`, Celery tasks | Pipeline (inline in tests) | [jobs](../jobs/README.md), [deployment/configuration](../deployment/configuration.md) | Partial |
| **FR-SCAN-09** Recurring schedules | `asset_scan_schedules`, beat task | `tests/test_asset_scan_schedules.py` | [scans](../scans/README.md) | Covered |

---

## 9–13. Scanner plugins — FR-HTTP / TLS / DNS / WHOIS / PORT

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-HTTP-01** HTTP headers | `app/plugins/http_headers/` | `app/plugins/http_headers/tests/` | [plugins](../plugins/README.md) | Covered |
| **FR-HTTP-02** Cookies | `app/plugins/cookies/` | `app/plugins/cookies/tests/` | Same | Covered |
| **FR-HTTP-03** Fingerprint | `app/plugins/fingerprint/` | `app/plugins/fingerprint/tests/` | Same | Covered |
| **FR-HTTP-04** robots / security.txt | `app/plugins/robots/`, `security_txt/` | Plugin test packages | Same | Covered |
| **FR-TLS-01** SSL certificates | `app/plugins/ssl/` | `app/plugins/ssl/tests/` | Same | Covered |
| **FR-TLS-02** TLS protocols/ciphers | `app/plugins/tls/` | `app/plugins/tls/tests/` | Same | Covered |
| **FR-DNS-01** DNS records + rules | `app/plugins/dns/` | `app/plugins/dns/tests/` | Same | Covered |
| **FR-WHOIS-01** WHOIS | `app/plugins/whois/` | `app/plugins/whois/tests/` | Same | Covered |
| **FR-PORT-01** Open ports | `app/plugins/ports/` | `app/plugins/ports/tests/` | Same | Covered |
| **FR-PORT-02** Optional Nmap `-sV` | Ports plugin collector | `app/plugins/ports/tests/` | FR-PORT-02, NFR-AVL-05 | Covered |

Cross-cutting: `app/core/rule_engine/tests/`, `tests/test_product_pipeline.py`.

---

## 14. Findings — FR-FND

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-FND-01** Normalized finding model | `app/findings/` | `app/findings/tests.py`, `tests/test_asset_findings.py`, pipeline | [findings](../findings/README.md) | Covered |
| **FR-FND-02** Severities | `FindingSeverity` enum | Findings / risk tests | [glossary](../glossary.md) | Covered |
| **FR-FND-03** Statuses | `FindingStatus` enum + APIs | Findings tests | [glossary](../glossary.md) | Covered |
| **FR-FND-04** List/filter project & asset | Findings routers | `tests/test_asset_findings.py` | [findings](../findings/README.md) | Covered |
| **FR-FND-05** Sources scan + monitoring | Findings + monitoring sync | `tests/test_monitoring.py`, findings sync | [findings](../findings/README.md), [monitoring](../monitoring/README.md) | Covered |
| **FR-FND-06** Reports read live findings | Report data collector | `tests/test_project_reports.py`, `tests/test_asset_reports.py` | [reports](../reports/README.md) | Covered |

---

## 15. Risk — FR-RSK

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-RSK-01** Severity point model | `app/core/risk_engine/` | `tests/test_risk_engine.py` | [risk](../risk/README.md), [scoring-model](../risk/scoring-model.md) | Covered |
| **FR-RSK-02** `security_score = max(0, 100 − points)` | Scoring module | `tests/test_risk_engine.py` | Same | Covered |
| **FR-RSK-03** Grade bands A+…F | `scoring.py` | `tests/test_risk_engine.py` | Same | Covered |
| **FR-RSK-04** Asset / project / org scores + history | Risk repos + metrics tables | `tests/test_risk_engine.py`, `tests/test_asset_risk_history.py` | [risk](../risk/README.md) | Covered |
| **FR-RSK-05** Recalc after scan | Post-scan risk hooks | Pipeline, risk tests | Same | Covered |
| **FR-RSK-06** AI must not compute score | AI prompts + risk separation | `app/services/ai/tests/`, risk docs | [architecture/ai](../architecture/ai.md), ADR risk/AI | Covered (policy + unit) |

---

## 16. AI — FR-AI

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-AI-01** Org-scoped chat (`ai:use`) | `app/services/ai/`, AI routers | `app/services/ai/tests/test_ai_service.py`, `tests/test_rbac.py`, pipeline | [ai](../ai/README.md) | Covered |
| **FR-AI-02** Persist conversations / usage | AI models | AI tests, `tests/test_org_isolation.py` | Same | Covered |
| **FR-AI-03** Facts-only prompts | AI context builders | AI unit tests | [architecture/ai](../architecture/ai.md) | Covered |
| **FR-AI-04** Offline when no `OPENAI_API_KEY` | AI service degrade path | AI tests (offline), pipeline | Same | Covered |
| **FR-AI-05** AI audit events | `ai.*` audit actions | Pipeline / audit catalog | [audit/event-catalog](../audit/event-catalog.md) | Partial |

---

## 17. Dashboard — FR-DASH

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-DASH-01** Live dashboard APIs | `app/dashboard/` | `tests/test_dashboard.py` | [dashboard](../dashboard/README.md) | Covered |
| **FR-DASH-02** Score, findings, assets, servers, activity | Dashboard service/repository | `tests/test_dashboard.py` | Same | Covered |
| **FR-DASH-03** Deep-links + hide scan actions | Frontend dashboard + RBAC | Backend API covered; UI Partial | Same | Partial |
| **FR-DASH-04** Generate-report entry RBAC | Frontend + `report:generate` | `tests/test_reports_rbac.py`, dashboard | Same | Partial |

Also: scan history / finding trend range APIs in `tests/test_dashboard.py`.

---

## 18. Reports — FR-RPT

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-RPT-01** PDF types executive/technical/weekly/monthly | `app/reports/` | `tests/test_project_reports.py`, `tests/test_asset_reports.py` | [reports](../reports/README.md), [glossary](../glossary.md) | Covered |
| **FR-RPT-02** Report status lifecycle | Report service / jobs | Report tests | [reports/generation-flow](../reports/generation-flow.md) | Covered |
| **FR-RPT-03** Collect findings + branding → PDF | Report collector + templates | Report tests | [reports/templates](../reports/templates.md) | Covered |
| **FR-RPT-04** AI or offline summary | Report AI summary path | Report / AI tests | [reports](../reports/README.md) | Covered |
| **FR-RPT-05** Auth preview/download (no public static) | Report download routes | Report tests, RBAC | [reports/api](../reports/api.md) | Covered |
| **FR-RPT-06** Delete report RBAC | Report delete | `tests/test_reports_rbac.py` | Same | Covered |
| **FR-RPT-07** List org / project / asset scope | Report list routers | Report tests | Same | Covered |

---

## 19. Monitoring — FR-MON

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-MON-01** Enroll on server asset types | `app/monitoring/` | `tests/test_monitoring.py` | [monitoring](../monitoring/README.md) | Covered |
| **FR-MON-02** One-time enrollment `sbe_…` | Enrollment service | `tests/test_monitoring.py` | Same | Covered |
| **FR-MON-03** Agent credential `sba_…` (never in UI) | Register flow | `tests/test_monitoring.py` | Same | Covered |
| **FR-MON-04** Agent auth (no user JWT / org header) | Agent routers | `tests/test_monitoring.py` | Same | Covered |
| **FR-MON-05** Read-only agent | `agent/` package | Agent security docs + monitoring tests | [agent/SECURITY.md](../../agent/SECURITY.md) | Policy + Covered |
| **FR-MON-06** Healthy / delayed / offline thresholds | Heartbeat + reconcile | `tests/test_monitoring.py` | [monitoring/agent](../monitoring/agent.md) | Covered |
| **FR-MON-07** Metrics history + UI cards | Metrics store + dashboard | `tests/test_monitoring.py`, `tests/test_dashboard.py` | Same | Covered |
| **FR-MON-08** Alerts vs findings separation | Alert engine + finding promotion | `tests/test_monitoring.py` | [findings](../findings/README.md) | Covered |
| **FR-MON-09** Revoke one agent credential | Monitoring revoke API | `tests/test_monitoring.py` | Same | Covered |

---

## 20. Audit — FR-AUD

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-AUD-01** Domain events `domain.action` | `event_bus`, `app/audit/events.py` | `tests/test_audit_logs.py`, pipeline | [audit](../audit/README.md), [glossary](../glossary.md) | Covered |
| **FR-AUD-02** Row fields + `resource_*` | Audit persist / models | `tests/test_audit_logs.py` | [audit](../audit/README.md), [database/tables](../database/tables.md) | Covered |
| **FR-AUD-03** Append-only (Postgres trigger) | Alembic `045`, immutability | Integrity tests on SQLite (mutate to prove detect); trigger itself Postgres-only | [security/audit](../security/audit.md) | Partial |
| **FR-AUD-04** Per-org hash chain + integrity API | Audit hash helpers | `tests/test_audit_logs.py` | [security/audit](../security/audit.md), ADR-009 | Covered |
| **FR-AUD-05** List / filter / export CSV|PDF | `app/audit/` routers | `tests/test_audit_logs.py` | [audit](../audit/README.md) | Covered |
| **FR-AUD-06** Fail-safe persist / SIEM | SAVEPOINT + independent subscribers | Audit tests + architecture | [architecture/events](../architecture/events.md) | Covered |
| **FR-AUD-07** No secrets in details | Audit publish conventions | Policy + review | [audit](../audit/README.md), NFR-SEC-30 | Policy |

---

## 21. SIEM — FR-SIEM

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **FR-SIEM-01** Forward after persist | SIEM subscriber | Thin / adapter unit (if present); fail-safe covered via audit path | [architecture/events](../architecture/events.md), [audit](../audit/README.md) | Partial |
| **FR-SIEM-02** Sinks none/syslog/splunk/elk/sentinel | `AUDIT_SIEM_SINK` adapters | Config + adapter code | [deployment/configuration](../deployment/configuration.md) | Partial |
| **FR-SIEM-03** Product usable with `none` | Default config | Default path in audit tests | FR-SIEM-03 | Covered |

---

## Non-functional requirements (NFR)

NFRs are traced at **control-group** granularity. Full shall-text: [non-functional-requirements.md](../product/non-functional-requirements.md).

### Security — NFR-SEC

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **NFR-SEC-01…04** Password hashing & policy | `app/core/security.py`, validators | `tests/test_auth.py` | [security](../security/README.md) | Covered |
| **NFR-SEC-05…08** JWT + hashed refresh | Auth / security modules | `tests/test_jwt_security.py`, `tests/test_auth.py` | [security/auth](../security/auth.md) | Covered |
| **NFR-SEC-09…13** Sessions, OTP/reset TTL, lockout, rate limits | Auth + Redis + SlowAPI | JWT/auth tests; lockout/rate Partial | Same | Partial |
| **NFR-SEC-14…16** Security headers, CORS, disable docs in prod | Middleware + settings | Startup / config (manual prod check) | [deployment/production](../deployment/production.md) | Policy |
| **NFR-SEC-17** Agent credential model | Monitoring enroll/register | `tests/test_monitoring.py` | [monitoring](../monitoring/README.md) | Covered |
| **NFR-SEC-18…20** Permission enforcement + no product superuser | `require_permission`, RBAC | `tests/test_rbac.py` | [security/rbac](../security/rbac.md) | Covered |
| **NFR-SEC-21…23** Logical multi-tenant isolation | `organization_id` + membership | `tests/test_org_isolation.py` | [security/tenancy](../security/tenancy.md) | Covered |
| **NFR-SEC-24…27** Input validation, enums, body size, plugin safety | Pydantic, nginx, plugin contract | Schema 422 paths across suites; nginx Compose config | [plugins/authoring](../plugins/authoring.md) | Covered / Policy |
| **NFR-SEC-28…31** Secrets via env; no secrets in audit/AI/SIEM | Settings, `.env.example` | Production validator (unit if present); policy review | [deployment/configuration](../deployment/configuration.md) | Policy |
| **NFR-SEC-32…34** Audit chain, audit API authz, structured app logs | Audit + logging stack | `tests/test_audit_logs.py` | [security/audit](../security/audit.md), [architecture/observability](../architecture/observability.md) | Covered / Partial |

### Performance — NFR-PERF

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **NFR-PERF-01** p95 &lt; 500 ms (non-scan) | FastAPI + Postgres design | **No CI assertion** | NFR-PERF-01 | Intent |
| **NFR-PERF-02…03** Rate limits + 20 MB body | SlowAPI, nginx | Config / Compose | [deployment](../deployment/README.md) | Policy |
| **NFR-PERF-04** Plugin timeouts | Plugin timeout settings | Plugin / orchestrator tests | [scan-engine](../scan-engine.md) | Covered |
| **NFR-PERF-05** AI timeout / token caps | AI settings | AI tests | [ai](../ai/README.md) | Partial |
| **NFR-PERF-06** Scans/reports off-request in non-dev | Celery flags | Jobs docs; inline in pytest | [jobs](../jobs/README.md) | Policy |
| **NFR-PERF-07** Agent heartbeat thresholds | Monitoring timers | `tests/test_monitoring.py` | [monitoring](../monitoring/README.md) | Covered |
| **NFR-PERF-08** No RPS claim | — | — | NFR-PERF-08 | Explicitly unspecified |

### Scalability — NFR-SCALE

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **NFR-SCALE-01…02** Horizontal API / workers | Stateless JWT + Celery + Redis | Architecture (no HA load test) | [architecture/system](../architecture/system.md), ADRs | Intent |
| **NFR-SCALE-03** Extensible plugins | Plugin registry | Plugin tests + authoring | [plugins/authoring](../plugins/authoring.md) | Covered |
| **NFR-SCALE-04…05** Postgres SoR; Redis queue/cache | Compose + settings | Integration via app tests | [database](../database/README.md) | Covered |
| **NFR-SCALE-06** Multi-region / sharding OOS | — | — | NFR-SCALE-06 | Explicitly unspecified |

### Availability — NFR-AVL

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **NFR-AVL-01…03** Redis down / ready / Celery | Health endpoints, Celery | Health checks (ops); limited unit | [deployment/troubleshooting](../deployment/troubleshooting.md) | Partial |
| **NFR-AVL-04…06** Plugin isolation / no Nmap / stubs off | Orchestrator + ports + future plugins | Scan engine / ports tests | [scan-engine](../scan-engine.md) | Covered |
| **NFR-AVL-07…08** AI degrade / no risk rollback | AI offline path | AI + risk tests | [ai](../ai/README.md) | Covered |
| **NFR-AVL-09…10** SIEM best-effort / optional | SIEM subscribers | Audit fail-safe | [architecture/events](../architecture/events.md) | Partial |
| **NFR-AVL-11…13** DB down / no fake cache / audit subordinate | Health ready, SAVEPOINT | Audit fail-safe tests | [security/audit](../security/audit.md) | Partial |
| **NFR-AVL-14…15** Backup ops / email dependency | Operator docs; Resend | No automated backup job | [deployment/backups](../deployment/backups.md) | Intent / Policy |

### Maintainability — NFR-MAINT

| Requirement | Implementation | Tests | Documentation | Coverage |
|-------------|----------------|-------|---------------|----------|
| **NFR-MAINT-01…03** Modular monolith, event bus, `/api/v1` | Package layout + frontend | Structural (code review) + suite | [architecture](../architecture/README.md), ADRs | Covered |
| **NFR-MAINT-04…06** Plugin interface + profiles + future stubs | Scan engine + plugins | Plugin tests | [plugins](../plugins/README.md) | Covered |
| **NFR-MAINT-07…08** Central config + Alembic | `config.py`, migrations | Migrate in deployment docs; SQLite `create_all` in tests | [deployment](../deployment/README.md), [database](../database/README.md) | Covered / Policy |
| **NFR-MAINT-09…11** Pytest coverage expectations | `make test` | The suite itself | [testing](../testing/README.md) | Covered |
| **NFR-MAINT-12…14** Docs as source of truth | `docs/product/` + folders | Doc review | [docs/README](../README.md), this matrix | Covered |

---

## Gaps called out by this matrix

Honest holes (also in [testing/gaps.md](../testing/gaps.md)):

| Gap | Related IDs |
|-----|-------------|
| No frontend unit/e2e suite | FR-DASH-03/04 UI bits; NFR-MAINT-10 |
| Ownership transfer / invite resend thin tests | FR-MEM-02, FR-MEM-06 |
| Postgres UPDATE/DELETE trigger not asserted on SQLite | FR-AUD-03, NFR-SEC-32 |
| SIEM adapters lightly tested | FR-SIEM-01/02 |
| Lockout / rate-limit / p95 not load-tested in CI | FR-AUTH-09/10, NFR-PERF-01 |
| Live OpenAI not called in CI | FR-AI-04 (offline path is) |

---

## Maintenance checklist

When shipping a requirement change:

1. Update the FR/NFR shall-text in `docs/product/`.
2. Implement in the listed module (or add a new module and update this row).
3. Add or extend pytest coverage; prefer `backend/tests/` for API/integration and `app/<module>/tests*` for unit.
4. Update the deep-dive docs and [glossary](../glossary.md) if enums/events change.
5. Set **Coverage** honestly (`Covered` / `Partial` / `Intent` / `Policy`).
6. If the capability is Future/stub, do **not** add an FR — keep it in [roadmap/planned](../roadmap/planned.md).

---

## Related

- [Functional requirements](../product/functional-requirements.md)
- [Non-functional requirements](../product/non-functional-requirements.md)
- [Testing inventory](../testing/inventory.md)
- [Testing gaps](../testing/gaps.md)
- [Architecture ADRs](../architecture/decisions/README.md)
