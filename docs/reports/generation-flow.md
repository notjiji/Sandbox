# Report Generation Flow

## User flow

```
Dashboard / Reports page
        │
        ▼
Generate Report modal
  · Project (org view) / Asset / Scan / Type
        │
        ▼
POST .../reports  { report_type, scan_id, generate: true }
        │
        ▼
Report record created (status: draft → generating)
        │
        ├── REPORT_RUN_INLINE=true  → sync pipeline (dev)
        └── REPORT_RUN_INLINE=false → Celery queue (prod)
        │
        ▼
Frontend polls list while status === "generating"
        │
        ▼
status: ready  →  Preview / Download
```

## Pipeline steps (`run_report_pipeline`)

File: `backend/app/core/report_engine/pipeline.py`

| Step | Function | Output |
|------|----------|--------|
| 1 | Set `status=generating` | DB update |
| 2 | `collect_report_data()` | `ReportData` |
| 3 | `generate_ai_summary()` | AI narrative on `ReportData` |
| 4 | `write_report_artifacts()` | PDF + HTML → durable storage (`local` volume or S3) |
| 5 | Update report | `status=ready`, `file_url` (storage key), `file_size`, `completed_at` |
| 6 | Audit | `report.generate` |

On failure: `status=failed`, exception propagated.

## Data collection (`collect_report_data`)

1. Load project and organization
2. Resolve scan (`report.scan_id` or latest for asset/project)
3. Query in-scope assets and open findings (optionally filtered by scan)
4. Compute severity breakdown, key risks, recommendations
5. Load org risk history for trend charts
6. Load `ScanPluginRun` rows for technical appendix
7. Build chart bar arrays for executive PDF
8. Resolve org branding from settings

## Background job

```python
# backend/app/jobs/reports.py
generate_report_task.delay(report_id=str(report.id))
```

Celery task name: `app.jobs.reports.generate_report`

## Storage

See [storage.md](./storage.md). Artifacts use keys `reports/{report_id}.pdf` and `.html` (`reports.file_url` stores the PDF key).

Access is only via:

- `GET .../reports/{id}/download` — authenticated PDF (streamed from storage backend)
- `GET .../reports/{id}/preview` — authenticated HTML (rendered on demand)

## Frontend status handling

- `useReportPolling` refreshes the list every 3s while any report has `status === "generating"`
- `GenerateReportModal` shows step progress during synchronous (inline) generation
- `AssetReportsTable` shows status badge, preview/download when `ready`, regenerate otherwise

## Development vs production

| Environment | `REPORT_RUN_INLINE` | Behavior |
|-------------|---------------------|----------|
| development | `true` (default) | User waits; modal shows steps |
| production | `false` (default) | Immediate API response; poll for completion |

Set explicitly in `.env` to override.
