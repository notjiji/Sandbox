# Agent security

The monitoring agent is an **outbound, read-only inspector**. It exists to report host state to Sandbox. It must not become a remote-control channel or an extra attack surface.

## Least privilege

Prefer read-only collection whenever possible.

The agent **does**:

- Read `/proc`, `psutil`, and package-manager query output
- Read firewall **status** (`ufw status`, `firewall-cmd --state`, `nft list`, `iptables -S`)
- Read SSH settings (`sshd -T` or config files)
- Read Fail2Ban and Docker facts
- Count pending updates without installing them
- Make outbound HTTPS calls to the platform API

The agent **does not**:

- Modify firewall rules
- Modify SSH configuration
- Install or upgrade packages
- Execute commands sent from the dashboard (there is no command channel)
- Upload arbitrary files
- Expose a remote shell or inbound listener
- Scan other hosts or networks

No platform component SSHs into customer infrastructure.

## Authentication

Agent API routes are separate from the user session API.

| Call | Credential |
|------|------------|
| `POST /monitoring/register` | One-time enrollment token `sbe_…` (15 minutes, single use) |
| `POST /monitoring/ingest` | Per-server `sba_…` Bearer token |

User JWTs and `X-Organization-ID` are not accepted on those routes. Revoking one server’s credential does not affect others.

## Commands the agent may run

`agent.collectors._util.run` is only for inspection. Collectors pass fixed argument lists (no shell interpolation, no dashboard-supplied strings).
