# Architecture

As-built system shape. Feature deep-dives (`docs/scan-engine.md`, `docs/plugins/`, `docs/audit/`, `docs/monitoring/`) remain valid for detail; this folder is the map.

| Document | Covers |
|----------|--------|
| [System](./system.md) | **Diagram A** (logical), runtime topology, request/scan/event flows |
| [Plugin architecture](./plugins.md) | **Diagram B** (orchestrator → registry → plugins → normalizer → findings → risk / AI) and the plugin contract |
| [Architecture decisions (ADRs)](./decisions/README.md) | Why FastAPI, Postgres, Celery, plugins, risk, AI, audit, tenancy, … |
| [Backend](./backend.md) | FastAPI modular monolith |
| [Frontend](./frontend.md) | React app and org-scoped API usage |
| [Scan engine](./scan-engine.md) | Orchestrator, plugins, jobs |
| [AI](./ai.md) | Chat and report summaries |
| [Events](./events.md) | In-process bus, audit, SIEM stub notifications |
| [Observability](./observability.md) | Logs, metrics, Compose monitoring stack |
