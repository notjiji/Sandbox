# Report Architecture

## Overview

Reporting is split into three layers so presentation can change without touching business logic:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  OrgReports / Reports / AssetReports / GenerateReportModal │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST (auth + X-Organization-ID)
┌───────────────────────────▼─────────────────────────────────┐
│                     Reports API                              │
│  router.py · asset_router.py · org_router.py                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   report_service.py                            │
│  CRUD · permissions · audit · download resolution              │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   Findings/Assets     report_engine/      Celery worker
   Scans/Risk         (data + pipeline)   jobs/reports.py
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
         ReportData                  Jinja2 templates
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    HTML → PDF (xhtml2pdf)
                            ▼
              backend/storage/reports/{id}.pdf
```

## Key modules

| Module | Path | Responsibility |
|--------|------|----------------|
| Models | `backend/app/reports/models.py` | SQLAlchemy `Report` entity |
| Service | `backend/app/reports/services/report_service.py` | Orchestration, RBAC, audit |
| Report engine | `backend/app/core/report_engine/` | Data collection, AI summary, rendering |
| Jobs | `backend/app/jobs/reports.py` | Async Celery task |
| Storage | `backend/storage/reports/` | PDF and HTML artifacts (private) |

## Design principles

1. **Data vs presentation** — `ReportData` is the single source of truth; templates only render it.
2. **Normalized findings** — The engine reads open findings from the database, not scanner code directly.
3. **AI on facts only** — `ai_summary.py` receives structured counts and top findings; it must not invent issues.
4. **No public file URLs** — Artifacts are retrieved only through authenticated API endpoints.

## Report types

| Type | Template | Audience |
|------|----------|----------|
| `executive` | `executive.html` | Managers, executives, clients |
| `technical` | `technical.html` | Analysts, developers, IT admins |

Weekly/monthly enum values exist for future use but share the executive template today.

## Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `REPORT_RUN_INLINE` | `true` in development | Sync generation vs Celery queue |
| Org `settings.branding` | See data-model | Logo, colors, footer in PDFs |
