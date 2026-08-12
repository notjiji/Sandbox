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
- Historical metrics (last 24 hours by default)
- Security-related alerts (high usage, weak SSH, inactive firewall, pending security updates)

## Quick start

1. Open a **server**, **Windows server**, or **Docker host** asset.
2. Go to **Monitoring** and click **Enroll agent**.
3. Copy the one-time token and install command.
4. Run the agent on the host. It heartbeats to `POST /api/v1/monitoring/ingest`.
5. Metrics and alerts appear on the asset page and the organization dashboard **Server health** panel.

## Security

- Agent tokens are opaque (`sba_…`), stored as SHA-256 hashes, and shown **once**.
- Ingest uses `Authorization: Bearer <agent token>` only — no user JWT and no `X-Organization-ID`.
- Rotate by enrolling again. Revoke immediately invalidates the current token.
- An agent is treated as offline if no heartbeat arrives for 10 minutes.
