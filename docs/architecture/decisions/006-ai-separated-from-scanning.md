# ADR-006 — AI separated from scanning

- **Status:** Accepted
- **Date:** 2026-08

## Context

AI can help explain findings and draft report summaries, but scanners must remain reliable when the model is down, unconfigured, or wrong. Mixing LLM calls into collect/parse would couple availability and correctness to a third-party provider.

## Decision

- **Scanning and risk** run without the LLM.
- **AI** reads structured snapshots (scores, counts, top issues, selected asset) for chat and optional report summaries.
- If `OPENAI_API_KEY` is empty or the provider fails, chat degrades and reports use an **offline template**; scan → findings → risk → PDF layout still work.

## Why

- Core assessment path stays deterministic and offline-capable.
- Prevents inventing vulnerabilities that plugins did not emit.
- Clear RBAC: `ai:use` is separate from `scan:run`.
- Cost and latency of LLM calls stay off the scan critical path.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| LLM inside each plugin | Brittle, expensive, hard to test |
| AI-required product | Blocks demos and air-gapped-ish ops |
| Fine-tuned local model in worker | Ops burden; not needed for V1 explanation |

## Consequences

- Empty `OPENAI_API_KEY` is a valid production posture for assessment-only deployments.
- AI quality depends on provider availability (documented limitation).
- Prompts must stay facts-only; product docs forbid score invention.
