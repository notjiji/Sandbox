# Later work (not implemented)

Candidates if the product continues. Order is not a schedule.

## Product surfaces

- API keys and machine authentication (then emit `admin.api_key_*`)
- Webhooks subscriber on the event bus
- Notification delivery (email / in-app) for the existing hook actions
- Org restore
- Billing
- SIEM configuration in the UI
- Dedicated audit explorer beyond Activity + export APIs

## Scanning

- Enable and complete cloud / kubernetes / malware plugins
- Stronger CVE (real inventory, not header hints only)
- Optional scan-authorization (DNS TXT, IP ownership) if the product must scan third-party space
- Multi-vantage DNS (called out as a plugin limitation, not a current feature)

## Platform

- Backup and restore runbook + jobs
- Production Compose/K8s without bind mounts and default Grafana passwords
- Frontend test suite
- Postgres-backed integration tests for triggers
- Performance budget and load tests
- Keep feature deep-dives (`docs/ai`, `docs/risk`, …) in lockstep with this source of truth

When a later item ships, move it into [product/scope](../product/scope.md) and delete it from this page — do not leave it as “planned” once it is in main.
