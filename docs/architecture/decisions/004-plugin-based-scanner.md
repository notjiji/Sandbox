# ADR-004 — Plugin-based scanner architecture

- **Status:** Accepted
- **Date:** 2026-08

## Context

Security checks span HTTP, TLS, DNS, WHOIS, ports, cookies, robots, security.txt, fingerprinting, and more. Hard-coding every check into one monolith function would freeze evolution and couple collectors to risk and UI.

## Decision

Scanners implement a **plugin contract** (collect → parse → rules → `ScanResult`). A **registry + orchestrator** loads plugins by profile (`quick` / `full` / `custom`), adapts assets to `ScanTarget`, and normalizes results into the shared **Finding** model.

Plugins do **not** own persistence, risk math, AI, or the dashboard.

## Why

- New checks ship as plugins without rewriting the orchestrator.
- Failures isolate: one plugin can fail without always failing the whole scan.
- Profiles map to slug lists in one place (`scans/profiles.py`).
- Disabled/future plugins (`cloud`, `kubernetes`, `malware`) can stay registered but off.

## Alternatives

| Option | Why not (for V1) |
|--------|------------------|
| Monolithic “run_all_checks()” | Unmaintainable; no profile story |
| External scanner microservices per check | Ops and latency cost; premature |
| Shelling out to arbitrary scripts | Security and reproducibility risk |

## Consequences

- Plugin authors must respect `ScanTarget` / `ScanResult` — no live ORM sessions in collectors.
- Nmap remains an optional host dependency inside the ports plugin.
- Inventory asset types can exist without a matching enabled plugin (documented limitation).
