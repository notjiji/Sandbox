# Report Templates

Templates live in `backend/app/core/report_engine/templates/`. Selected by `renderer.py` based on `report_type`.

## Template selection

| Report type | Template file |
|-------------|---------------|
| `executive`, `weekly`, `monthly` | `executive.html` |
| `technical` | `technical.html` |

## Rendering pipeline

```
ReportData  →  Jinja2 template  →  HTML  →  xhtml2pdf  →  PDF
                                      ↓
                              {id}.html (stored alongside PDF)
```

Renderer: `backend/app/core/report_engine/renderer.py`

## Executive template sections

| # | Section | Data fields |
|---|---------|-------------|
| Cover | Logo, org, project, score box | `branding`, `score`, `assessment_date` |
| 1 | Executive summary | `score`, `severity_distribution`, `asset_counts` |
| 2 | Security posture | `severity_bars`, `trend_chart`, `plugin_bars` |
| 3 | Key risks | `key_risks` |
| 4 | Recommendations | `recommendations` |
| 5 | Security trend | `score.previous`, `score.current`, `score.change` |
| 6 | Asset overview | `asset_counts` |
| 7 | AI summary | `ai_summary` |
| Conclusion | Footer, contact | `branding.footer_text`, `branding.contact_email` |

### Charts

Chart bars use nested HTML tables (xhtml2pdf-compatible):

- **`severity_bars`** — Critical / High / Medium / Low horizontal bars
- **`trend_chart`** — Last 6 org risk history points
- **`plugin_bars`** — Top 8 finding categories by scanner plugin

Built in `data.py` via `_build_bar_chart()`, `_severity_bars()`, `_plugin_bars()`, `_trend_chart()`.

## Technical template sections

| # | Section |
|---|---------|
| 1–4 | Overview, scope, assets, methodology |
| 5–8 | Findings summary by severity |
| 11 | Detailed findings with evidence |
| 12 | Scanner results (`scanner_results` or plugin fallback) |
| 13 | Remediation plan |
| 14 | AI analysis |
| 15 | Appendix with scanner execution detail |

Uses `branding.primary_color` for headings and supports org logo.

## Branding variables

Available in all templates as `data.branding`:

| Variable | Source |
|----------|--------|
| `organization_name` | `organizations.name` |
| `logo_url` | `organizations.logo_url` |
| `primary_color` | `settings.branding.primary_color` (default `#7c3aed`) |
| `contact_email` | `settings.branding.contact_email` |
| `footer_text` | `settings.branding.footer_text` |

Configure in **Organization Settings → Branding**.

## Fallback PDF

If xhtml2pdf fails, `renderer.py` falls back to a minimal text PDF via `build_text_pdf()` so generation still completes.
