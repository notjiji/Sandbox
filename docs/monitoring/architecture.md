# Monitoring architecture

```
Linux / Docker host
        │
        │ collectors + security modules
        ▼
 Monitoring Agent
        │
        │ 1. POST /monitoring/register   (short-lived sbe_… enrollment token)
        │ 2. receives per-server sba_… credential; enrollment token invalidated
        │ 3. POST /monitoring/ingest     (Bearer sba_…)
        ▼
 Monitoring API ── metrics, security checks, alert engine, database ──► Dashboard
```

The platform **does not SSH** into servers. Each server has its own credential. Revoking Server A does not affect Server B.

## Registration

```
User → Add server → Install agent
  → short-lived enrollment token (sbe_…)
  → curl …/install.sh | sudo bash
  → agent registers
  → permanent per-server credential (sba_…) stored on the host
  → enrollment token invalidated
  → server shows ONLINE
```

Enrollment tokens expire in 15 minutes and are single-use. They cannot ingest metrics.

## Components

| Component | Role |
|-----------|------|
| `MonitoringAgent` | One identity per asset. Enrollment hash, credential hash, status. |
| `MonitoringMetric` | Normalized time-series: `metric_type`, `value`, `unit`, `collected_at`. New collectors add a type, not a column. |
| `MonitoringSnapshot` | Heartbeat document (JSON payload for services, security, processes). |
| `MonitoringAlert` | Deduped by `(asset_id, alert_code)`. |
| Collectors | CPU, memory, disk, uptime, processes, Docker, system. |
| Security modules | Firewall, SSH, Fail2Ban, updates. |

## Normalized metrics

Numeric collector output is stored as rows, not per-metric columns:

```
monitoring_metrics
  id
  asset_id      -- server
  metric_type
  value
  unit
  collected_at
  labels        -- optional, e.g. {"filesystem": "/var"}
```

Built-in `metric_type` values:

| Type | Unit | Notes |
|------|------|--------|
| `cpu_usage` | percent | |
| `memory_usage` | percent | |
| `disk_usage` | percent | one row per filesystem via `labels` |
| `load_average` | ratio | 1-minute load |
| `uptime` | seconds | |

Add types such as `memory_used` or `process_count` without a schema change. `labels` distinguishes dimensions (mounts) without extra tables.

## Status

| Status | Meaning |
|--------|---------|
| `pending` | Install command issued; waiting for register |
| `online` | Registered; heartbeat within 10 minutes |
| `offline` | Last seen more than 10 minutes ago |
| `revoked` | This server's credential destroyed |

## Code map

| Layer | Path |
|-------|------|
| Models | `backend/app/monitoring/models.py` |
| Agent API | `backend/app/monitoring/agent_router.py` |
| Enrollment | `backend/app/monitoring/router.py` |
| Agent | `agent/agent/` |
| UI | `frontend/src/features/monitoring/` |
