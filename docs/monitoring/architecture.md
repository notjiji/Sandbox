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
| Collectors | CPU, memory, disk, network, uptime, processes, Docker, system. |
| Security modules | Firewall, SSH, Fail2Ban, updates (read-only). |

## Data model

The server **is** an `Asset` (`server` / `windows_server` / `docker_host`). There is no parallel `servers` table.

```
Organization
    │
    ▼
Project
    │
    ▼
Asset (server)
    │
    ├── monitoring_agents          -- enrollment + per-server credential
    ├── monitoring_metrics         -- time-series (CPU, RAM, disk, load, network)
    ├── monitoring_snapshots       -- latest services, containers, security payload
    └── monitoring_alerts          -- operational (CPU, disk, offline)
             │
             ▼
         findings (source=monitoring)
             │
             ▼
         Risk Engine
```

| Conceptual table | Implementation |
|------------------|----------------|
| Servers | `assets` (monitorable types) |
| ServerAgents | `monitoring_agents` |
| ServerMetrics | `monitoring_metrics` |
| ServerServices | latest `monitoring_snapshots.payload.metrics.services` |
| ServerContainers | latest snapshot `security.docker` |
| ServerSecurityChecks | latest snapshot `security.*` + `findings` |
| ServerAlerts | `monitoring_alerts` |

Services, containers, and security checks are **current state** (snapshot). Numeric history lives in `monitoring_metrics` so new collectors add a `metric_type`, not a table.

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
| `network_rx` / `network_tx` | bytes_sec | throughput since previous heartbeat |
| `uptime` | seconds | |

History charts (CPU, RAM, disk, network, load) read these series. `GET .../monitoring/metrics?hours=24` returns points for graphing.

Add types such as `memory_used` or `process_count` without a schema change. `labels` distinguishes dimensions (mounts) without extra tables.

## Security findings vs alerts

**Alert** — something is happening now (CPU, disk, server offline). Stored in `monitoring_alerts`.

**Finding** — a security condition exists (insecure SSH, pending security updates). Stored in the shared `findings` table (`source=monitoring`) and scored by the risk engine.

```
Internet Scanner ──► findings ──► Risk Engine ◄── findings ◄── Server Monitoring
                                              ▲
                                              └── alerts stay operational
```

| Field | Example finding |
|-------|-----------------|
| `source` | `monitoring` |
| `plugin` | `monitoring` |
| `category` | `server_security` |
| `finding_code` | `SSH_PASSWORD_AUTH` |
| `severity` | `medium` |
| `evidence` | `PasswordAuthentication=yes` |
| `recommendation` | Disable password authentication… |

`scan_id` is null for monitoring findings. Risk recalculates only when a finding opens or resolves (not every heartbeat).

## Status

The agent heartbeats every **30 seconds**. Liveness is computed from `last_seen_at` on read (`delayed` is not stored). `SERVER_OFFLINE` opens only at the offline threshold.

| Age since last heartbeat | Status | Alert |
|--------------------------|--------|-------|
| < 1 minute | `online` | none |
| 1–5 minutes | `delayed` | none |
| ≥ 5 minutes | `offline` | `SERVER_OFFLINE` |

| Status | Meaning |
|--------|---------|
| `pending` | Install command issued; waiting for register |
| `online` | Registered; last heartbeat within 1 minute |
| `delayed` | Heartbeat missed; last seen 1–5 minutes ago |
| `offline` | Last seen more than 5 minutes ago |
| `revoked` | This server's credential destroyed |

## Code map

| Layer | Path |
|-------|------|
| Models | `backend/app/monitoring/models.py` |
| Agent API | `backend/app/monitoring/agent_router.py` |
| Enrollment | `backend/app/monitoring/router.py` |
| Agent | `agent/agent/` |
| UI | `frontend/src/features/monitoring/` |
| Dashboard servers | `frontend/src/features/monitoring/components/ServerHealthPanel.tsx` |
