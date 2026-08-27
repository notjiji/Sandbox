# Glossary and naming conventions

Canonical terms for documentation, APIs, and database columns. Prefer these spellings everywhere. When code accepts aliases, document the **canonical** form first.

Source of enums: `backend/app/*/enums.py`. Event names: `backend/app/audit/events.py`. Normalization: `backend/app/events/names.py`.

---

## Rules of thumb

| Layer | Convention | Example |
|-------|------------|---------|
| Audit / domain events | `{domain}.{verb}` lowercase snake after the dot | `asset.create` |
| Database columns | `snake_case` | `resource_type`, `resource_id` |
| API JSON / query params | `snake_case` | `scan_type`, `entity_type` (alias) |
| Enum **values** (wire / DB) | lowercase `snake_case` strings | `security_analyst`, `in_review` |
| Enum **members** (Python) | `SCREAMING_SNAKE` | `OrganizationRole.SECURITY_ANALYST` |
| Human UI labels | Title Case | Security Analyst |

Do **not** invent parallel spellings in docs (`asset.created`, `asset_create`, `ASSET_CREATE` as the primary name).

---

## Audit actions (canonical)

**Canonical:** dot-separated `{domain}.{action}` — e.g. `asset.create`, `scan.completed`.

| Avoid as primary docs spelling | Prefer |
|--------------------------------|--------|
| `ASSET_CREATED` | `asset.create` |
| `asset.created` | `asset.create` |
| `asset_create` | `asset.create` |
| `SCAN_COMPLETED` | `scan.completed` |

**Accepted input aliases** (normalized before persist):

- Screaming snake constants: `ASSET_CREATED` → `asset.create`, `SCAN_COMPLETED` → `scan.completed`
- Python `AuditAction` attribute names map to the same string values

Full catalog: [audit/event-catalog.md](./audit/event-catalog.md).

---

## Resource identity (DB vs API)

| Concept | Database / hash payload | Audit list/export API |
|---------|-------------------------|------------------------|
| Kind of thing | **`resource_type`** | Query/response alias: **`entity_type`** |
| Thing id | **`resource_id`** | Query/response alias: **`entity_id`** |

Mapping (always):

```
entity_type  →  resource_type
entity_id    →  resource_id
```

- Persistence and hash chain use **`resource_type` / `resource_id` only**.
- HTTP filters on `GET /api/v1/audit-logs` accept `entity_type` / `entity_id` and map them to those columns.
- Publish helpers accept either pair; if both are passed, `resource_*` wins.

Do **not** document `entity_type` as a physical Postgres column.

Common `resource_type` values: `asset`, `project`, `organization`, `scan`, `finding`, `report`, `user`, …

---

## Organization roles

| Wire / DB value | Python member | UI label |
|-----------------|---------------|----------|
| `owner` | `OWNER` | Owner |
| `admin` | `ADMIN` | Admin |
| `security_analyst` | `SECURITY_ANALYST` | Security Analyst |
| `manager` | `MANAGER` | Manager |
| `viewer` | `VIEWER` | Viewer |

Source: `OrganizationRole` in `backend/app/members/enums.py`.

Member status values: `invited`, `active`, `suspended`, `removed`.

---

## Scan statuses

| Value | Meaning |
|-------|---------|
| `pending` | Created, not queued |
| `queued` | Waiting for worker / run |
| `running` | Orchestrator executing |
| `completed` | Finished (may be partial plugin success) |
| `failed` | Failed |
| `cancelled` | Cancelled by user |

Scan types: `quick`, `full`, `custom`.

Plugin run statuses: `pending`, `running`, `completed`, `failed`, `skipped`.

Document these as lowercase. Avoid `COMPLETED` / `FAILED` in prose unless quoting a Python enum member.

---

## Finding statuses

| Value |
|-------|
| `open` |
| `in_review` |
| `resolved` |
| `false_positive` |
| `accepted` |

---

## Finding severity

| Value |
|-------|
| `critical` |
| `high` |
| `medium` |
| `low` |
| `info` |

Audit log **event** severity (separate enum on audit rows): `info`, `warning`, `error`, `critical`.

Do not confuse finding severity with audit severity.

---

## Asset types

Wire values (lowercase):

`website`, `domain`, `public_ip`, `server`, `windows_server`, `docker_host`, `cloud_account`, `kubernetes_cluster`, `api_endpoint`, `mobile_application`, `git_repository`, `email_domain`, `s3_bucket`, `azure_subscription`

Asset status: `pending`, `active`, `archived`, `deleted`.

Ownership verification (when used):

- Methods: `domain`, `dns_txt`, `http`, `ip_ownership`
- Statuses: `unverified`, `pending`, `verified`, `failed`

---

## Report types and statuses

| Report type | Value |
|-------------|-------|
| Executive | `executive` |
| Technical | `technical` |
| Weekly | `weekly` |
| Monthly | `monthly` |

Report status: `draft`, `generating`, `ready`, `failed`.

---

## Other recurring terms

| Term | Meaning |
|------|---------|
| Organization | Tenant; selected via `X-Organization-ID` |
| Project | Container for assets inside an org |
| Asset | Scannable / inventoriable target |
| Finding | Normalized issue from a scan or monitoring promotion |
| Risk score | Deterministic 0–100 security score (higher = better) |
| Plugin | Scanner module returning `ScanResult` |
| Modular monolith | Single FastAPI deployable with domain modules |

---

## Documentation checklist

When writing or reviewing docs:

1. Events → `asset.create` style  
2. DB columns → `resource_type` / `resource_id`  
3. API audit filters → mention `entity_type` / `entity_id` **as aliases**  
4. Roles / statuses / types → lowercase wire values  
5. Link here if introducing a new enum value

Related: [audit README](./audit/README.md), [database tables](./database/tables.md), [architecture events](./architecture/events.md).
