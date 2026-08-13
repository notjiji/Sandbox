# Sandbox monitoring agent

Lightweight outbound HTTPS agent. The platform never SSHs into customer servers.

Each server has its own credential. The install command only contains a **short-lived enrollment token** (`sbe_…`). On first start the agent exchanges that token for a permanent per-server credential (`sba_…`) stored locally, and the enrollment token is invalidated.

```
security-agent/
├── agent/
│   ├── main.py
│   ├── config.py
│   ├── collectors/     # cpu, memory, disk, network, uptime, processes, services, docker, system
│   ├── security/       # firewall, ssh, fail2ban, updates (read-only)
│   └── client/api.py
├── requirements.txt
├── Dockerfile
├── SECURITY.md
└── README.md
```

## Install

From the dashboard **Install agent** action:

```bash
curl -fsSL http://localhost:8000/api/v1/monitoring/install.sh | \
  sudo env SANDBOX_API_URL=http://localhost:8000/api/v1 SANDBOX_ENROLLMENT_TOKEN=sbe_... bash
```

Or, after copying this directory to the host:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SANDBOX_API_URL=https://your-platform.example/api/v1
export SANDBOX_ENROLLMENT_TOKEN=sbe_...
python -m agent
```

The enrollment token expires in 15 minutes and can be used **once**. After registration, the credential is written to `$SANDBOX_AGENT_HOME/credential` (default `~/.sandbox-agent/credential`).

## Docker

```bash
docker build -t sandbox-agent .
docker run --rm \
  -e SANDBOX_API_URL=https://your-platform.example/api/v1 \
  -e SANDBOX_ENROLLMENT_TOKEN=sbe_... \
  sandbox-agent
```

## Environment

| Variable | Purpose |
|----------|---------|
| `SANDBOX_API_URL` | API origin including `/api/v1` |
| `SANDBOX_ENROLLMENT_TOKEN` | One-time install token (`sbe_…`) |
| `SANDBOX_AGENT_CREDENTIAL` | Optional override of the stored `sba_…` credential |
| `SANDBOX_AGENT_HOME` | State directory (credential file) |
| `SANDBOX_AGENT_INTERVAL` | Heartbeat seconds (default 30) |
| `SANDBOX_AGENT_TIMEOUT` | HTTP timeout (default 15) |

## Security

The agent is outbound HTTPS only and **read-only**. It does not take commands from the dashboard, change firewall/SSH, install software, or open a remote shell. See [SECURITY.md](./SECURITY.md).
