# Reports Documentation

Phase 9 security assessment reporting for the Sandbox platform.

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | System design and component boundaries |
| [data-model.md](./data-model.md) | Database schema and `ReportData` structure |
| [api.md](./api.md) | REST endpoints, permissions, and examples |
| [templates.md](./templates.md) | Jinja2 PDF templates and branding |
| [generation-flow.md](./generation-flow.md) | End-to-end report generation pipeline |

## Quick start

1. User opens **Reports** (`/reports`) or clicks **Generate Report** on the dashboard.
2. Select project, asset, scan, and report type (Executive or Technical).
3. API creates a report record with `status=generating` and queues a Celery job (or runs inline in development).
4. Worker collects findings, builds `ReportData`, generates AI summary, renders HTML, converts to PDF, stores in `backend/storage/reports/`.
5. Report appears in the library with `status=ready`. Preview and download require authentication and `REPORT_READ`.

## Security

- PDFs are **never** served from a public static path.
- Download and preview require a valid session, organization context, and `REPORT_READ`.
- All generate/download/delete actions are audit-logged.
