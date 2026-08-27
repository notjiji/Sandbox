# ADR-005 — Deterministic risk scoring

- **Status:** Accepted
- **Date:** 2026-08

## Context

Customers and auditors need a **repeatable** security score. If the score moves because a model “felt” differently, trust collapses. AI is useful for explanation, not for inventing posture numbers.

## Decision

Compute security score with a **deterministic risk engine**:

- Open findings contribute fixed severity/rule weights from `risk_rules` (and severity fallbacks).
- `security_score = max(0, 100 - total_risk_points)`.
- Letter grades map from fixed thresholds (A+ … F).
- Scores persist at asset, project, and organization levels with history.

The AI assistant **must not** compute or override this number.

## Why

- Same inputs → same score (testable, explainable in reports).
- Rule catalog can evolve via Alembic-seeded `risk_rules` without changing the formula shape.
- Separates “what is wrong” (findings) from “how bad is the posture” (risk).

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| LLM-assigned score | Non-deterministic; unauditable |
| Only CVSS aggregation | Incomplete for config/header/DNS findings |
| Vendor black-box rating | No control over weights |

## Consequences

- Changing rule weights changes scores — treat catalog edits as product decisions.
- Resolved / false-positive / accepted findings do not count as open risk.
- AI prompts are constrained to structured facts about stored scores.
