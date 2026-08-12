# Monitoring agent

The agent lives in `agent/` and only makes outbound HTTPS calls.

## Install on the server

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SANDBOX_API_URL=https://your-platform.example/api/v1
export SANDBOX_AGENT_TOKEN=sba_...
python -m sandbox_agent
```

The dashboard **Enroll agent** action prints this command with a one-time token.

## Behavior

- Collects CPU, RAM, disk, uptime, processes (via `psutil`).
- On Linux, reads `/etc/ssh/sshd_config` and probes ufw/firewalld, Fail2Ban, Docker, and apt security updates when those tools exist.
- Missing checks are omitted (`null`) instead of failing the heartbeat.
- Posts to `/monitoring/ingest` every 60 seconds (or `next_interval_seconds` from the API).
- Backs off on transport errors; exits cleanly on SIGINT/SIGTERM.

## What not to do

- Do not open inbound SSH from the Sandbox backend.
- Do not put the agent token in source control or screenshots after the enroll modal is dismissed.
- Do not send a user access token to the ingest endpoint.
