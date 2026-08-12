# Monitoring agent

Modular Python service in `agent/`. Collectors and security checks are separate plugins. The agent only makes outbound HTTPS calls.

## Install

Dashboard **Install agent** prints:

```bash
curl -fsSL https://your-platform.example/api/v1/monitoring/install.sh | \
  sudo env SANDBOX_API_URL=https://your-platform.example/api/v1 SANDBOX_ENROLLMENT_TOKEN=sbe_... bash
```

That command contains a **short-lived enrollment token**, not the permanent credential.

On first start the agent:

1. `POST /monitoring/register` with the enrollment token
2. Receives a per-server credential (`sba_…`)
3. Stores it in `~/.sandbox-agent/credential` (mode 0600)
4. Heartbeats with `Authorization: Bearer sba_…`

The enrollment token is then invalid.

## Layout

```
agent/
├── agent/
│   ├── main.py
│   ├── config.py
│   ├── collectors/   # cpu, memory, disk, uptime, processes, docker, system
│   ├── security/     # firewall, ssh, fail2ban, updates
│   └── client/api.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## What not to do

- Do not SSH from the Sandbox backend into customer servers.
- Do not put a permanent `sba_…` credential in the install command or chat logs.
- Do not share one credential across servers. Revoke is per server.
- Do not send a user JWT to register or ingest.
