# Risk Scoring Model

**Security Score ranges from 0–100, with higher values representing a stronger security posture.**

A score of **100** means no open-finding penalties. A score of **0** means penalties reached or exceeded 100 points. The AI assistant **never** computes this number; it may only explain a stored score.

Live engine: `backend/app/core/risk_engine/` (`scoring.py`, `engine.py`). Rule weights live in the `risk_rules` table (seeded by Alembic). Catalog of codes: [risk-rules.md](./risk-rules.md).

---

## Severity

Open findings carry one of:

| Severity | Default points (fallback) |
|----------|---------------------------|
| `info` | 0 |
| `low` | 5 |
| `medium` | 15 |
| `high` | 30 |
| `critical` | 50 |

Source: `SEVERITY_POINTS` in `backend/app/core/risk_engine/scoring.py`.

When a plugin emits a finding, `RiskEngine.resolve_finding()` looks up `risk_rules` by `(plugin, finding_code)`:

- **Hit:** use the row’s `severity` and `score` (the rule **weight**).
- **Miss:** use the plugin’s severity hint, or `medium` if none, and the fallback points above.

`SEVERITY_WEIGHTS` in `backend/app/core/risk_engine/weights.py` (`critical=10`, `high=7`, …) is **not** used by the live engine. Do not document it as the product formula.

---

## Rule weights

Each enabled `risk_rules` row has a `score` float. That value is stored on the finding as `risk_score` and is the penalty for that issue while the finding stays `open`.

Examples from the seeded table (full catalog in [risk-rules.md](./risk-rules.md)):

| Rule | Severity | Weight |
|------|----------|--------|
| Missing CSP (`HTTP_NO_CSP`) | high | 25 |
| Expired certificate (`SSL_EXPIRED`) | critical | 50 |
| TLS 1.0 (`SSL_TLS10_ENABLED`) | high | 30 |
| Telnet open (`PORT_TELNET_OPEN`) | critical | 45 |

Weights are **not** always equal to the severity fallback (CSP is high but 25, not 30). Always prefer `risk_rules.score`.

---

## Penalties

```
total_risk_points = sum(risk_score of every OPEN finding in the bundle)
security_score    = max(0, 100 - total_risk_points)
```

Only `status=open` findings add points. `in_review`, `resolved`, `false_positive`, and `accepted` do **not** penalize.

`FindingCheckStatus.PASSED` plugin results never become persisted findings (`resolve_finding` returns `None`).

There is **no** extra penalty for finding age, SLA, or “display penalty” layers.

---

## Aggregation

| Level | Bundle | How scores combine |
|-------|--------|--------------------|
| **Asset** | All findings for that `asset_id` | Sum open `risk_score` → `security_score = max(0, 100 − total)` |
| **Project** | All findings for that `project_id` | **Same additive formula** on the project’s findings (not the average of asset scores) |
| **Organization** | Latest **scanned** asset scores | **Arithmetic mean** of those asset `score` values. Unscanned assets are counted but **excluded from the average**. |

Asset criticality (`critical` / `high` / `medium` / `low`) is used to **rank** top issues (`prioritize_findings`). It does **not** multiply the live `security_score`. `RiskCalculator.score_findings()` can apply `CRITICALITY_RISK_MULTIPLIERS` (4 / 2 / 1 / 0.25); that helper is **not** the snapshot path.

---

## Normalization

- Score is clamped to **[0, 100]** (`max(0, 100 − points)`). There is no upper bound other than 100; more than 100 points still displays **0**.
- Grades and “risk level” labels are derived from the **normalized score**, not from raw points.
- Org trend compares the current overall score to the previous history row (`compute_trend`): delta **> 1** → `improving`, **< −1** → `declining`, else `stable`.
- `org.risk_score_changed` is audited when the absolute change is **≥ 0.1**.

---

## Grades (A+ through F)

`grade_from_security_score()`:

| Score | Grade |
|------:|:------|
| ≥ 95 | A+ |
| ≥ 90 | A |
| ≥ 80 | B |
| ≥ 70 | C |
| ≥ 60 | D |
| < 60 | F |

Separate **risk level** label (`risk_level_from_security_score`): ≥ 90 Excellent, ≥ 75 Good, ≥ 60 Fair, ≥ 40 Poor, else Critical. That is not the letter grade.

---

## Asset score

`calculate_asset_risk` → `asset_risk` row (`total_risk`, `score`, `grade`, severity counts). Recalculated after a scan (`recalculate_after_scan`) and after monitoring security findings (`recalculate_after_monitoring`).

Assets with no snapshot are **unscanned** (`scanned=false`) in org dashboards. They do not pull the org average down; they increment `unscanned_assets`.

---

## Organization score

`calculate_organization_risk`:

1. Load latest `asset_risk` per asset in the org.
2. Average `score` across **scanned** assets only.
3. Sum `total_risk` across those assets (informational).
4. Upsert `organization_risk` (1:0..1) and append `organization_risk_history`.

If nothing is scanned, overall score is unset (`None` / not assessed).

---

## Historical score

| Store | Meaning |
|-------|---------|
| `organization_risk_history` | One row per org recalculation: `overall_score`, `total_risk`, `grade`, `calculated_at` |
| `asset_risk` | Multiple rows per asset over time; APIs use the **latest** |
| `project_risk_metrics` | Snapshot rows; latest used at read |

Dashboard trend: `change = current − previous` from org history. Reports copy scores at generation time; the dashboard reads live tables.

---

## When scores update

- Scan completed (findings persisted → asset, project, org).
- Monitoring security findings written (same three levels).
- Finding status changes take effect on the **next** calculation (not a live trigger on every PATCH unless a caller invokes the engine).

---

## Not in V1

- Per-org custom severity weights
- Criticality multipliers on the stored score
- Time-decay / SLA risk
- AI-invented scores
