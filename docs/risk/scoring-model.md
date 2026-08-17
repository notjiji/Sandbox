# Risk Scoring Model

## Inputs

1. **Open findings** — weighted by severity and `risk_score`
2. **Asset criticality** — metadata on the asset record
3. **Risk rules** — optional adjustments from `risk_rules` table

## Asset score

The live engine is `backend/app/core/risk_engine/` (`security_score = max(0, 100 - total_risk_points)`). Severity points: info 0, low 5, medium 15, high 30, critical 50. Higher remaining score is more secure.

`RiskCalculator.score_findings()` in `backend/app/risk/calculator.py` is a helper on the same 0–100 scale; do not treat it as a second scoring product.

Open findings accumulate points; resolved/false-positive/accepted rows are not treated as open risk in the engine snapshots.

## Rollup

**Project:** Average (or weighted average) of asset scores in the project.

**Organization:** Aggregates across all projects in the org, stored in `OrganizationRisk` with a snapshot appended to `OrganizationRiskHistory` on recalculation.

## When scores update

- After scan completion (findings persisted → risk recalculation triggered)
- Manual finding status changes may affect next calculation
- Org history grows over time for trend charts

## Dashboard vs report

Both consume the same underlying risk tables:

| Consumer | Source |
|----------|--------|
| Dashboard `/overview` | Latest org risk + history |
| Report `ReportData.score` | Computed from in-scope assets at generation time |
| Report trend charts | `list_organization_risk_history()` |

Reports snapshot scores at generation time; dashboard shows live values.

## Recommendations

`Recommendation` rows map finding codes to standardized remediation text. Plugins and the rule engine reference these codes for consistent guidance across findings and reports.

## Future considerations

- Custom severity weights per organization
- Asset criticality multipliers in project rollup
- SLA-based risk decay for aged findings

These are not implemented in V1 but the `RiskRule` model supports extension.
