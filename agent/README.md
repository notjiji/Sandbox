# Sandbox monitoring agent

Outbound HTTPS agent that reports host health and a basic security posture. The platform never SSHs into customer servers.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Use the token shown once when you enroll a server in the dashboard:

```bash
export SANDBOX_API_URL=https://your-platform.example/api/v1
export SANDBOX_AGENT_TOKEN=sba_...
python -m sandbox_agent
```

Optional:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SANDBOX_AGENT_INTERVAL` | `60` | Seconds between heartbeats |
| `SANDBOX_AGENT_TIMEOUT` | `15` | HTTP timeout |

The agent authenticates with `Authorization: Bearer <token>` only. Do not send a user JWT or `X-Organization-ID`.

## What it reports

CPU, RAM, disk, uptime, top processes, Docker, firewall, SSH config, Fail2Ban, available updates, and system info. Linux-only checks are skipped when the tools are missing (including on Windows for local development).

## systemd (optional)

```ini
[Unit]
Description=Sandbox monitoring agent
After=network-online.target

[Service]
Type=simple
Environment=SANDBOX_API_URL=https://your-platform.example/api/v1
Environment=SANDBOX_AGENT_TOKEN=sba_...
WorkingDirectory=/opt/sandbox-agent
ExecStart=/opt/sandbox-agent/.venv/bin/python -m sandbox_agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
