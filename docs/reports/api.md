# Reports API

Base path: `/api/v1`. All endpoints require:

- `Authorization: Bearer <access_token>`
- `X-Organization-ID: <org_uuid>` (except auth-only routes)

Interactive OpenAPI docs: `/docs` (non-production).

## Organization scope

### List all reports

```
GET /organizations/current/reports
```

Query parameters:

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default 1) |
| `limit` | int | Page size (default 20, max 100) |
| `report_type` | string | `executive` or `technical` |
| `status` | string | `draft`, `generating`, `ready`, `failed` |
| `project_id` | uuid | Filter by project |
| `search` | string | Search name/description/project |

Permission: `REPORT_READ`

## Project scope

Prefix: `/projects/{project_id}/reports`

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/` | REPORT_READ | List project reports |
| POST | `/` | REPORT_GENERATE | Create report (`generate: true` queues pipeline) |
| GET | `/{report_id}` | REPORT_READ | Get metadata |
| PATCH | `/{report_id}` | REPORT_GENERATE | Update name/description |
| GET | `/{report_id}/preview` | REPORT_READ | HTML preview |
| GET | `/{report_id}/download` | REPORT_READ | PDF download (authenticated) |
| POST | `/{report_id}/generate` | REPORT_GENERATE | Generate draft report |
| POST | `/{report_id}/regenerate` | REPORT_GENERATE | Re-run pipeline |
| DELETE | `/{report_id}` | REPORT_DELETE | Delete report + files |

### Create report body

```json
{
  "report_type": "executive",
  "asset_id": "uuid-optional",
  "scan_id": "uuid-optional",
  "name": "optional title",
  "generate": true
}
```

## Asset scope

Prefix: `/projects/{project_id}/assets/{asset_id}/reports`

Same operations as project scope where applicable (list, create, preview, download, regenerate). Asset is implicit on create.

## Permissions matrix

| Role | Generate | View/Download/Preview | Delete |
|------|----------|----------------------|--------|
| owner, admin, security_analyst | ✓ | ✓ | ✓ |
| manager | ✓ | ✓ | — |
| viewer | — | ✓ | — |

## Response: `ReportSummary`

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "project_name": "Production",
  "asset_id": "uuid-or-null",
  "scan_id": "uuid-or-null",
  "report_type": "executive",
  "report_version": 1,
  "name": "Executive Report — Example Site",
  "status": "ready",
  "file_url": null,
  "file_size": 84210,
  "created_by": "uuid",
  "created_by_name": "Jane Doe",
  "created_at": "2026-08-10T16:32:00Z",
  "completed_at": "2026-08-10T16:32:05Z"
}
```

## Security notes

- There is **no** public download route. `/api/v1/reports/download` does not exist.
- PDF files under `backend/storage/reports/` are not mounted as static files.
- Download requests are audit-logged as `report.download`.

## Audit events

| Action | Event name |
|--------|------------|
| Create | `report.create` |
| Generate | `report.generate` |
| Regenerate | `report.regenerate` |
| Download | `report.download` |
| Delete | `report.delete` |
