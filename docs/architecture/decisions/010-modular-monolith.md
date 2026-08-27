# ADR-010 — Modular monolith over microservices

- **Status:** Accepted
- **Date:** 2026-08

## Context

The product has many domains (auth, orgs, assets, scans, findings, risk, reports, AI, audit, monitoring). Splitting each into a deployable microservice early would multiply ops cost before product-market fit.

## Decision

Ship a **modular monolith**: one FastAPI deployable, one Postgres, clear module boundaries (`backend/app/<domain>/`), plus Celery workers that import the same codebase. Frontend is a separate SPA. Compose runs process roles (API, worker, beat), not a mesh of domain services.

## Why

- Shared transactions and finding/risk consistency without distributed sagas.
- Single Alembic history and deployment artifact for the API.
- Modules can still grow toward extraction later if needed.
- Matches team size and V1 scope.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Microservices per domain | Network boundaries, versioning, and distributed tracing cost |
| Serverless functions per route | Awkward for long scans and shared plugin state |
| Separate “scan service” repo only | Duplicates models/auth; premature |

## Consequences

- Discipline required: no cross-module deep coupling; prefer events for side effects (ADR-007).
- Horizontal scale is by replicating API/worker processes, not by independently deploying “findings service.”
- Known limitation: no in-repo Kubernetes microservice topology.
