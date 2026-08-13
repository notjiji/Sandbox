# Server Monitoring

Phase 10 connects authorized Linux (and Docker host) servers through an **outbound HTTPS agent**. The platform never SSHs into customer infrastructure.

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | Agent → API → dashboard flow |
| [api.md](./api.md) | Enrollment, ingest, and overview endpoints |
| [agent.md](./agent.md) | Installing and running the agent |

## What the dashboard shows

- CPU, RAM, and disk usage
- Disk space and uptime
- Running processes
- Docker, firewall, SSH, Fail2Ban, and available updates
- Basic system information
- Historical metrics (CPU, RAM, disk, network, load over 24 hours)
- Security-related **findings** (weak SSH, inactive firewall, pending security updates)
- Operational **alerts** (high CPU/disk, server offline)

## Quick start

1. Open a **server**, **Windows server**, or **Docker host** asset.
2. Go to **Monitoring** and click **Install agent**.
3. Run the generated `curl … \| bash` command on the server (enrollment token expires in 15 minutes, one use).
4. The agent registers, stores its own credential, and the server shows **Online**.
5. Metrics and alerts appear on the asset monitoring page and the organization dashboard **Servers** section.

## Security

- Enrollment uses a short-lived `sbe_…` token (15 minutes, single-use). The permanent `sba_…` credential is issued only to that server and never shown in the UI.
- Each server has its own credential. Revoking one host does not affect others.
- Ingest uses `Authorization: Bearer <per-server credential>` — no user JWT and no `X-Organization-ID`.
- Agents heartbeat every 30 seconds. Missed heartbeats show **Delayed** after 1 minute and **Offline** after 5 minutes (`SERVER_OFFLINE` alert).
