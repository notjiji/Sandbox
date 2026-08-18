# Product Definition

Sandbox is a **Security Intelligence Platform** for organizations that already manage the infrastructure they assess.

This page is the product brief. Implementation detail lives in [goal](./goal.md), [users](./users.md), [scope](./scope.md), and [functional requirements](./functional-requirements.md). If a plugin, route, or README in the repo looks like a feature, this document decides whether it is **V1** or **Future**.

## Product

**Security Intelligence Platform** (Sandbox).

A multi-tenant workspace where a team inventories internet-facing assets, runs authorized scans, reviews normalized findings, sees a deterministic security score, explains results with AI, publishes reports, monitors enrolled servers, and keeps an auditable activity trail.

## Problem

Organizations often have **fragmented visibility** into their internet-facing security posture.

Typical symptoms:

- Asset inventory lives in spreadsheets, DNS consoles, and cloud portals that never agree.
- HTTP, TLS, DNS, WHOIS, and port checks are run as one-off tools with no shared finding model.
- Risk is a slide in a meeting, not a repeatable score tied to evidence.
- Reports are assembled by hand; explanations depend on whoever ran the last scan.
- Server health and scan findings are different products, so nobody sees both.
- There is no tenant-scoped audit trail of who scanned, who changed membership, or who generated a report.

Sandbox exists to close that gap for **assets the organization already owns or operates**. It is not a general-purpose attack platform and it does not prove third-party IP ownership.

## Solution

A centralized platform that:

1. **Manages assets** — inventory, types, hierarchy, tags, and project grouping.
2. **Scans authorized infrastructure** — plugin-based HTTP, SSL/TLS, DNS, WHOIS, and port checks against active assets in the tenant.
3. **Normalizes security findings** — one finding model (severity, status, evidence, plugin) regardless of scanner.
4. **Calculates deterministic security scores** — rule-based points and letter grades; the AI assistant does not invent the score.
5. **Explains findings with AI** — org-scoped chat over structured facts when an API key is configured.
6. **Generates reports** — executive, technical, weekly, and monthly PDFs.
7. **Monitors authorized servers** — read-only agent on enrolled server-like assets.
8. **Maintains an auditable activity trail** — append-only, hash-chained logs with optional SIEM export.

## Target users

Users are **global accounts**. Access to tenant data comes from an **organization membership** and one of five roles. A person can belong to several organizations with different roles.

| Persona | Typical role | Job |
|---------|--------------|-----|
| Security lead / founder | `owner` | Owns the tenant, people, and posture outcome |
| Platform / IT admin | `admin` | Runs the workspace day to day |
| Security analyst / engineer | `security_analyst` | Scans, triages, monitors, reports |
| Engineering or compliance manager | `manager` | Reads posture, ships reports, asks AI |
| Auditor / stakeholder | `viewer` | Read-only evidence |

Role permissions are defined in [users](./users.md) and [RBAC](../rbac/roles-and-permissions.md). Below is what each persona **needs from the product**, not the permission matrix.

### 1. Security lead / founder (`owner`)

Responsible for the organization’s security program and for the Sandbox tenant itself.

**Needs:**

- Create and configure the organization; transfer ownership; archive the tenant.
- Invite owners of other functions and set roles without becoming the scan operator.
- A single dashboard that answers “how exposed are we?” with a score, not a pile of tool exports.
- An activity trail they can stand behind in an audit.
- Reports they can send to leadership without rebuilding slides.

They do not need to run every scan. They need control, accountability, and a defensible summary.

### 2. Platform / IT admin (`admin`)

Keeps the workspace usable: members, projects, assets, and settings. Cannot delete the organization, change billing permission, or transfer ownership.

**Needs:**

- Member lifecycle: invite, role change, suspend, remove.
- Project structure that matches how the company actually groups systems.
- Asset inventory that stays current (types, tags, bulk actions, hierarchy).
- Ability to run scans and manage monitoring agents when the security team is small.
- Org settings and activity without owner-only destroy actions.

They need administration of the platform, not a second SIEM console.

### 3. Security analyst / engineer (`security_analyst`)

The primary operator of assessment and monitoring.

**Needs:**

- Register and update assets they are authorized to assess.
- Run quick, full, or custom scans (HTTP, SSL/TLS, DNS, WHOIS, ports, related surface checks).
- A normalized finding queue with review states (open, in review, resolved, false positive, accepted).
- A score they can explain from rules and evidence, not from a model guess.
- AI explanations and remediation framing on top of those facts.
- Enroll and revoke the monitoring agent on server / Windows server / Docker host assets.
- Generate and delete PDF reports for a project or asset.

They need a closed loop: inventory → scan → finding → score → report. They do not need malware detonation, threat feeds, or cloud/K8s posture in V1.

### 4. Engineering or compliance manager (`manager`)

Accountable for delivery or compliance, not for running scanners.

**Needs:**

- Read dashboard, assets, scans, findings, and monitoring without mutating inventory.
- Generate reports for a sprint review, customer questionnaire, or compliance packet.
- Ask the AI assistant about current org facts (`ai:use`); cannot run scans or enroll agents.
- A score and grade they can quote without re-interpreting raw plugin output.

They need visibility and export, not operator controls.

### 5. Auditor / stakeholder (`viewer`)

External or internal reader who must see evidence and must not change it.

**Needs:**

- Read-only dashboard, assets, scan history, findings, reports, and monitoring.
- Confidence that scores and findings were produced by the platform, not edited in place.
- No AI chat (`ai:use` is omitted), no scan runs, no member or asset changes.

They need a witness surface. They do not need a workstation.

---

## 2. MVP vs Future

The repository already contains **future stubs** (disabled plugins under `backend/app/plugins/future/`, event-bus subscribers that only log, catalogued audit names with no emitter). Those files are not shipped product.

**V1** means implemented in backend and, unless noted, exposed in the UI. **Future** means stub, preview, or not built — do not demo it as a capability.

| Capability | V1 | Reality in this repo |
|------------|:--:|----------------------|
| Authentication | ✅ | Register, OTP, login, refresh, logout, password reset, lockout, session revoke |
| Organizations | ✅ | Multi-tenant orgs, settings, membership, `X-Organization-ID` |
| Projects | ✅ | CRUD, archive/restore; container for assets, scans, findings, reports |
| Asset management | ✅ | Inventory, types, hierarchy, links, tags, bulk actions. Some types are inventory-only (no dedicated scanner) |
| HTTP scanning | ✅ | Headers, cookies, fingerprint, robots.txt, security.txt |
| SSL/TLS | ✅ | Certificate and protocol plugins |
| DNS | ✅ | Record and misconfiguration checks |
| WHOIS | ✅ | Domain registration data |
| Port scanning | ✅ | Ports plugin; Nmap `-sV` when `nmap` is on PATH, otherwise still runs without it |
| Risk engine | ✅ | Deterministic points and grades A+–F; not computed by AI |
| AI assistant | ✅ | Org-scoped chat over structured facts; live model needs `OPENAI_API_KEY` |
| Dashboard | ✅ | Org security intelligence, findings breakdown, activity, monitoring cards |
| Reports | ✅ | PDF generate / preview / download / delete |
| Server monitoring | ✅ | Read-only agent on `server`, `windows_server`, `docker_host` |
| Audit | ✅ | Meaningful events, per-org hash chain, export, integrity API |
| SIEM adapters | ✅ | Syslog, Splunk, ELK, Sentinel via `AUDIT_SIEM_SINK` (default `none`) |
| Malware analysis | Future | `plugins/future/malware` — loaded, `enabled=False` |
| Threat intelligence | Future | No feed, IOC, or reputation product |
| CVE intelligence | Future | `plugins/future/cve` is a **limited OSV lookup from HTTP/service hints**, not package inventory or a CVE platform. Treat full CVE intelligence as unshipped |
| Cloud security | Future | `plugins/future/cloud` — `enabled=False`; cloud asset types can be inventoried only |
| Kubernetes security | Future | `plugins/future/kubernetes` — `enabled=False` |
| Webhooks | Future | Event bus mentions a subscriber; **not built** |
| Analytics | Future | No analytics product. Dashboard risk summaries are V1; bus “analytics” subscriber is a stub |

### How to read stubs

- **Disabled plugins** (`malware`, `cloud`, `kubernetes`) are registered so the loader stays stable. They are not V1 scanners.
- **CVE** lives under `future/` even though the plugin defaults to enabled on the **full** profile. That is a hint-based lookup, not the CVE intelligence capability in the table above.
- **Notifications** log a hook; there is no email or in-app delivery.
- **`org:billing`** exists on the owner role; there is no billing product.
- **API keys** are catalogued as audit names only; they are not issued.

When a Future row ships, move it to V1 here and in [scope](./scope.md), and remove it from [roadmap/planned](../roadmap/planned.md). Do not leave a stub documented as if it were released.

## Related

- [Goal](./goal.md) — what the platform optimizes for, and what it is not
- [Scope](./scope.md) — as-built vs later, including asset-type coverage
- [Functional requirements](./functional-requirements.md) — behavior as implemented
- [Roadmap](../roadmap/README.md) — later work, not a schedule
