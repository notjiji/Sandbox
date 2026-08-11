# Risk Scoring

The risk engine aggregates findings and asset exposure into scores and letter grades at the asset, project, and organization levels.

## Score hierarchy

```
Findings (per asset)
    → AssetRisk (score + grade)
    → ProjectRiskMetric
    → OrganizationRisk + OrganizationRiskHistory
```

Used by: dashboard, reports, org risk API.

## Grades

| Score range | Grade |
|-------------|-------|
| 90–100 | A |
| 80–89 | B |
| 70–79 | C |
| 60–69 | D |
| < 60 | F |

Applied in both risk service and report data collector.

## API

Base: `/api/v1/organizations/risk`

| Endpoint | Description |
|----------|-------------|
| GET `/` | Current organization risk |
| GET `/dashboard` | Dashboard-oriented metrics |
| GET `/assets/{asset_id}` | Single asset risk |

Permission: typically `org:read` / project access via membership.

## Models

| Model | Purpose |
|-------|---------|
| `AssetRisk` | Latest score per asset |
| `ProjectRiskMetric` | Project-level rollup |
| `OrganizationRisk` | Current org score |
| `OrganizationRiskHistory` | Trend data points |
| `RiskRule` | Rule metadata for scoring |
| `Recommendation` | Remediation templates |

Path: `backend/app/risk/models.py`

## Key modules

| Module | Path |
|--------|------|
| Calculator | `backend/app/risk/calculator.py` |
| Service | `backend/app/risk/service.py` |
| Repository | `backend/app/risk/repositories/risk_repository.py` |
| Core engine | `backend/app/core/risk_engine/` |

## Trend calculation

Dashboard and reports compare `current` score to `previous` from `OrganizationRiskHistory`:

- `change = current - previous`
- `trend = improving | declining | stable`

## Unscanned assets

Assets without a completed scan may show as unscanned with no score. Dashboard tracks `scanned_assets` vs `unscanned_assets`.

## Scoring model detail

[scoring-model.md](./scoring-model.md)
