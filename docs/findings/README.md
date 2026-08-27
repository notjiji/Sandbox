# Findings

Findings are normalized security issues produced by scanner plugins and the rule engine. They are the primary data source for dashboards, reports, and risk scoring.

## Lifecycle

```
Plugin ScanResult
    → ScanNormalizer
    → RuleEngine (catalog rules)
    → findings table (linked to scan, asset, project)
    → review workflow (`open` → `in_review` → `resolved` / `false_positive` / `accepted`)
```

## Core fields

| Field | Description |
|-------|-------------|
| `title` | Human-readable issue name |
| `finding_code` | Stable identifier (e.g. `SSL_CERT_EXPIRED`) |
| `severity` | `critical`, `high`, `medium`, `low`, `info` |
| `risk_score` | Numeric score used in aggregation |
| `status` | `open`, `in_review`, `resolved`, `false_positive`, `accepted` |
| `plugin` | Source scanner plugin or `monitoring` for agent findings |
| `source` | `scan` (default) or `monitoring` |
| `category` | Grouping such as `server_security` |
| `evidence` | Reproducible proof |
| `recommendation` | Remediation guidance |
| `scan_id` / `asset_id` / `project_id` | Scope linkage (`scan_id` null for monitoring) |

Wire values for statuses and severity: [glossary.md](../glossary.md).

## Monitoring as a finding source

Security conditions from the agent become findings. Operational events stay as alerts.

```
Agent heartbeat
  → alert_engine     → monitoring_alerts   (CPU, disk, offline)
  → finding_engine   → findings            (SSH, firewall, security updates)
                     → risk engine
```

Example monitoring finding:

| Field | Value |
|-------|-------|
| `source` | `monitoring` |
| `plugin` | `monitoring` |
| `category` | `server_security` |
| `finding_code` | `SSH_PASSWORD_AUTH` |
| `title` | SSH Password Authentication Enabled |
| `evidence` | `PasswordAuthentication=yes` |
| `recommendation` | Disable password authentication… |

Scanner and monitoring findings both contribute to asset, project, and organization risk scores.

Model: `backend/app/findings/models.py`

## API

Project scope: `/api/v1/projects/{project_id}/findings`

Asset scope: `/api/v1/projects/{project_id}/assets/{asset_id}/findings`

| Action | Permission |
|--------|------------|
| List / get | `finding:read` |
| Update status | `finding:update` |
| Review workflow | `finding:review` |

## Frontend

- Project findings: `/projects/:projectId/findings`
- Asset findings: `/projects/:projectId/assets/:assetId/findings`
- Dashboard deep links: `?severity=critical`

## Reports integration

The report engine reads **open findings** for the selected scan scope via `collect_report_data()` — findings are never duplicated into report rows at generation time.

See [../reports/data-model.md](../reports/data-model.md).

## Audit

Finding updates and reviews emit `finding.update` and `finding.review` events.

## Key files

| Layer | Path |
|-------|------|
| Models | `backend/app/findings/models.py` |
| Repository | `backend/app/findings/repositories/finding_repository.py` |
| Router | `backend/app/findings/router.py` |
| Frontend | `frontend/src/features/findings/` |

## Finding model in scan engine

Documented in [../scan-engine.md](../scan-engine.md) under the findings persistence section.
