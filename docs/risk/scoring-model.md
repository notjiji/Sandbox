# Risk Scoring Model

## Inputs

1. **Open findings** — weighted by severity and `risk_score`
2. **Asset criticality** — metadata on the asset record
3. **Risk rules** — optional adjustments from `risk_rules` table

## Asset score

`RiskCalculator.score_findings()` in `backend/app/risk/calculator.py` combines finding severities into a 0–100 score where higher is better (more secure).

Typical weighting:

- Critical findings penalize heavily
- Multiple medium/low findings accumulate
- Resolved findings are excluded (only `open` status counts)

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
