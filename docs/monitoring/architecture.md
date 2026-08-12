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
| `MonitoringSnapshot` | Time-series metrics plus JSON payload. |
| `MonitoringAlert` | Deduped by `(asset_id, alert_code)`. |
| Collectors | CPU, memory, disk, uptime, processes, Docker, system. |
| Security modules | Firewall, SSH, Fail2Ban, updates. |

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
