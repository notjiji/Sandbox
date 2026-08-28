# Observability (as built)

## Application

- `setup_logging` on API and Celery (`sandbox-api` / `sandbox-worker`).
- Request logging middleware; request/correlation IDs.
- `prometheus_fastapi_instrumentator` exposes `/metrics` on the **backend** (internal Docker network).
- **Production:** nginx returns 404 for `/metrics` on the public edge; Prometheus scrapes `backend:8000/metrics` directly (see `infrastructure/monitoring/prometheus.yml`).
- Health: `/health` (process up), `/health/live`, `/health/ready` (Postgres `SELECT 1` + Redis `PING`).

## Compose stack

| Component | Default URL / port |
|-----------|-------------------|
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (`GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`, default admin/admin) |
| Loki | http://localhost:3100 |
| Promtail | Reads Docker socket, ships to Loki |
| postgres-exporter / redis-exporter | Scraped by Prometheus |

`make monitoring` prints Grafana/Prometheus/Loki URLs.

This stack is **local observability**, not a hosted APM product. Alerting rules in Grafana are whatever is provisioned under `infrastructure/monitoring/grafana/`; do not assume pager integration.

## Audit vs ops logs

`audit_logs` are a **compliance/activity** trail. They are not application error logs. Failed Celery tasks emit structured logs via `task_failure` (`background job failed`, `job_type`, `timed_out`) — see [deployment/workers.md](../deployment/workers.md).
