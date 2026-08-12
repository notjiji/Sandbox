# Monitoring architecture

```
Linux / Docker host
        │
        │ local collection (psutil, sshd_config, ufw, fail2ban, docker)
        ▼
 Monitoring Agent  ── HTTPS POST /api/v1/monitoring/ingest ──►  Monitoring API
        │                                                         │
        │ Bearer sba_… token                                      ├── Metrics Service
        │ (hash stored, plaintext shown once)                     ├── Security Checks
                                                                  ├── Alert Engine
                                                                  └── Database
                                                                         │
                                                                         ▼
                                                                      Dashboard
```

The platform **does not SSH** into servers. The customer installs a small agent that pushes snapshots on a timer (default 60 seconds).

## Components

| Component | Role |
|-----------|------|
| `MonitoringAgent` | One enrolled agent per asset. Token hash, status, last seen. |
| `MonitoringSnapshot` | Time-series metrics plus JSON payload (processes, security checks). |
| `MonitoringAlert` | Deduped by `(asset_id, alert_code)`. Auto-resolved when the condition clears. |
| Alert engine | Thresholds and posture checks evaluated on every ingest. |
| Dashboard | Asset monitoring page and org-wide server health panel. |

## Status

| Status | Meaning |
|--------|---------|
| `pending` | Enrolled, waiting for the first heartbeat |
| `online` | Heartbeat within the last 10 minutes |
| `offline` | Last seen more than 10 minutes ago (computed lazily) |
| `revoked` | Token destroyed; ingest returns 401 |

## Alert codes (V1)

| Code | Trigger |
|------|---------|
| `CPU_HIGH` | CPU ≥ 90% |
| `RAM_HIGH` | RAM ≥ 90% |
| `DISK_HIGH` | Disk ≥ 90% |
| `DISK_CRITICAL` | Disk ≥ 95% |
| `FIREWALL_INACTIVE` | Firewall reported disabled |
| `SSH_ROOT_LOGIN` | `PermitRootLogin` enabled |
| `SSH_PASSWORD_AUTH` | Password authentication enabled |
| `FAIL2BAN_INACTIVE` | Fail2Ban not running |
| `UPDATES_AVAILABLE` | Security updates > 0 |

## Code map

| Layer | Path |
|-------|------|
| Models | `backend/app/monitoring/models.py` |
| Ingest | `backend/app/monitoring/agent_router.py` |
| Enrollment | `backend/app/monitoring/router.py` |
| Agent | `agent/sandbox_agent/` |
| UI | `frontend/src/features/monitoring/` |
