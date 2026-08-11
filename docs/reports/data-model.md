# Report Data Model

## Database: `reports` table

Defined in `backend/app/reports/models.py`. Migration `038_report_pipeline_fields` adds pipeline columns.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `project_id` | UUID FK | Owning project |
| `asset_id` | UUID FK (nullable) | Scoped asset, if any |
| `scan_id` | UUID FK (nullable) | Source scan for findings |
| `report_type` | enum | `executive`, `technical`, `weekly`, `monthly` |
| `report_version` | int | Template/data schema version (default `1`) |
| `name` | string | Display title |
| `description` | text | Optional notes |
| `status` | enum | `draft`, `generating`, `ready`, `failed` |
| `file_url` | string (nullable) | **Not a public URL** — reserved, always `null` after generation |
| `file_size` | bigint | PDF size in bytes |
| `completed_at` | timestamptz | When generation finished |
| `created_by` | UUID FK | User who requested the report |
| `created_at` / `updated_at` | timestamptz | Standard timestamps |

## Application model: `ReportData`

Built by `collect_report_data()` in `backend/app/core/report_engine/data.py`. Consumed by templates and AI summary.

```
ReportData
├── report_id, report_type, report_version, title, assessment_date
├── organization { id, name, slug }
├── project { id, name }
├── scan { id, scan_type, status, completed_at } | null
├── branding { organization_name, logo_url, primary_color, contact_email, footer_text }
├── score { current, previous, change, grade, trend }
├── severity_distribution { critical, high, medium, low, info }
├── severity_bars[]          ← chart-ready severity bars
├── plugin_bars[]            ← findings by scanner/plugin
├── trend_chart[]            ← historical score bars
├── trend_points[]
├── asset_counts { total, websites, domains, ips, servers }
├── assets[]
├── findings[]               ← normalized open findings
├── key_risks[]              ← top critical/high
├── recommendations[]
├── findings_by_plugin{}
├── scanner_results[]        ← technical appendix (ScanPluginRun)
├── ai_summary
└── generated_by
```

### Finding shape (normalized)

Each entry in `findings` / `key_risks`:

| Field | Source |
|-------|--------|
| `id`, `title`, `severity`, `description`, `evidence`, `recommendation` | `findings` table |
| `asset_name` | Joined `assets` |
| `plugin`, `finding_code`, `risk_score` | Finding record |
| `first_detected`, `last_detected` | `detected_at`, `updated_at` |

## Organization branding

Stored in `organizations.settings.branding` (JSONB):

```json
{
  "primary_color": "#7c3aed",
  "contact_email": "security@example.com",
  "footer_text": "Confidential — authorized recipients only."
}
```

Logo uses top-level `organizations.logo_url`.
