# ADR-003 — Why Celery

- **Status:** Accepted
- **Date:** 2026-08

## Context

Scans and PDF reports can run longer than an HTTP request should block. Scheduled work (due scan schedules, agent offline reconcile) needs a clock. Development still wants a fast inner loop.

## Decision

Use **Celery** with **Redis** as broker/result backend for workers and beat. Allow **inline** execution (`SCAN_RUN_INLINE` / `REPORT_RUN_INLINE`) when `ENVIRONMENT=development` so local Compose can run scans without waiting on a healthy worker.

## Why

- Mature Python task queue that shares the FastAPI codebase and settings.
- Beat scheduler covers recurring asset schedules without a second orchestration product.
- Production defaults force queued execution so API processes stay responsive.
- Redis was already required for rate limiting and lockout counters.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Only inline / background threads | No durable queue; dies with the API process |
| RQ | Weaker beat/scheduling story for our presets |
| Temporal / Cadence | Excellent for workflows; too heavy for V1 |
| Kafka consumers | Overkill for scan/report jobs |

## Consequences

- Exactly **one** Celery beat instance should run.
- Redis loss drops in-flight queues (acceptable — not business SoR).
- Operators must monitor `celery-worker` when inline mode is off (production).
- Debugging requires checking both API and worker logs depending on inline flags.
