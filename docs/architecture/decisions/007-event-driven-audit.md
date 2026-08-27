# ADR-007 — Event-driven audit architecture

- **Status:** Accepted
- **Date:** 2026-08

## Context

Security products need an activity trail (who scanned, who invited, who generated a report) without coupling every service to SIEM SDKs or failing business writes when logging fails.

## Decision

Use an **in-process event bus**. Domain actions publish named events (`asset.create`, `scan.completed`, …). Subscribers run in order:

1. Persist to `audit_logs` (hash chain, fail-safe SAVEPOINT)
2. Optional SIEM forward (`AUDIT_SIEM_SINK`)
3. Notification hook (log only in V1)

Publishers do not know about SIEM or webhooks.

## Why

- One publish site per domain action; new sinks do not require editing every service.
- Audit persist failure must not roll back the business transaction (SAVEPOINT).
- SIEM is best-effort; product works with sink `none`.
- Avoids operating Kafka/NATS for V1 volumes.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Direct `INSERT` only in each service | Duplicated SIEM/notification wiring |
| Outbox + Kafka | Correct at scale; premature for V1 |
| Dual-write to SIEM in request path | Couples UX to SIEM latency/outages |

## Consequences

- Bus is **not** durable cross-process messaging; workers that need audit still go through the same helpers/API DB session patterns.
- Webhooks and analytics consumers are explicitly future (known limitation).
- Activity feed and audit search are different API shapes over the same underlying events.
