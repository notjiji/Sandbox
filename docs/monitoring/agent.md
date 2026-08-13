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
4. Heartbeats every 30 seconds with `Authorization: Bearer sba_…`

The enrollment token is then invalid.

## Layout

```
agent/
├── agent/
│   ├── main.py
│   ├── config.py
│   ├── collectors/   # cpu, memory, disk, uptime, processes, services, docker, system
│   ├── security/     # firewall, ssh, fail2ban, updates
│   └── client/api.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## What it collects

Each heartbeat sends a `metrics` object. Collectors live in `agent/agent/collectors/`. The API stores numeric series in a shared `monitoring_metrics` table (`metric_type`, `value`, `unit`, `collected_at`) so new collectors do not need new columns.

### CPU

```json
{
  "cpu_usage": 73.4,
  "load_1m": 2.14,
  "load_avg": [2.14, 1.88, 1.52],
  "cores": 4
}
```

`cpu_percent` is also sent for backward compatibility (same value as `cpu_usage`).

### Memory

```json
{
  "total_mb": 8192,
  "used_mb": 5412,
  "available_mb": 2780,
  "usage_percent": 66.1
}
```

### Disk (per filesystem)

```json
{
  "disks": [
    {
      "filesystem": "/",
      "total_gb": 100.0,
      "used_gb": 72.0,
      "available_gb": 28.0,
      "usage_percent": 72.0
    },
    {
      "filesystem": "/var",
      "total_gb": 50.0,
      "used_gb": 42.0,
      "available_gb": 8.0,
      "usage_percent": 84.0
    }
  ],
  "disk_percent": 72.0
}
```

The alert engine evaluates **each mount** independently:

| Usage | Severity | Alert code example |
|-------|----------|--------------------|
| ≥ 80% | Warning (medium) | `DISK_WARN__var` |
| ≥ 90% | High (high) | `DISK_HIGH__root` |
| ≥ 95% | Critical (critical) | `DISK_CRITICAL__data` |

Thresholds are fixed for now; per-org configuration is planned.

### Network

Read-only interface counters via `psutil`. The agent stores the previous sample locally and sends **bytes per second** (receive and transmit). No sockets are opened.

```json
{
  "network_rx_bytes_sec": 12800.0,
  "network_tx_bytes_sec": 3200.0
}
```

The first heartbeat has no rate (no previous sample). Charts plot receive and transmit over 24 hours.

### Uptime

```json
{
  "boot_time": "2026-07-26T10:12:00+00:00",
  "uptime_seconds": 1480320,
  "last_reboot_at": "2026-07-26T10:12:00+00:00"
}
```

The dashboard renders uptime as e.g. `17 days 04h 32m`.

### Running services (Linux systemd)

Facts only — name + status. No expected/unexpected or malware classification in V1.

```json
{
  "services": [
    { "name": "nginx", "status": "RUNNING" },
    { "name": "postgresql", "status": "RUNNING" },
    { "name": "docker", "status": "RUNNING" },
    { "name": "ssh", "status": "RUNNING" },
    { "name": "fail2ban", "status": "RUNNING" }
  ]
}
```

### Docker (when installed)

Sent under `security.docker`:

```json
{
  "installed": true,
  "running": true,
  "version": "24.0.7",
  "containers": 12,
  "containers_running": 10,
  "containers_stopped": 2,
  "images": 15,
  "container_list": [
    { "name": "web", "status": "running", "image": "nginx:latest" }
  ]
}
```

### Firewall (read-only)

Detects UFW → firewalld → nftables → iptables. Never modifies rules.

```json
{
  "enabled": true,
  "backend": "ufw",
  "default_incoming": "DENY",
  "default_outgoing": "ALLOW"
}
```

### SSH security (read-only)

Prefers effective config from `sshd -T`, otherwise parses `sshd_config` (+ includes). Never changes settings.

```json
{
  "permit_root_login": false,
  "permit_root_login_raw": "prohibit-password",
  "password_authentication": true,
  "password_authentication_raw": "yes",
  "pubkey_authentication": true,
  "pubkey_authentication_raw": "yes",
  "port": 22,
  "protocol": "2",
  "config_source": "sshd -T"
}
```

Example alert:

- **SSH Password Authentication Enabled** (MEDIUM)
- Current: `PasswordAuthentication yes`
- Recommendation: disable passwords; use key-based auth

### Fail2Ban

```json
{
  "installed": true,
  "running": true,
  "jails": ["sshd", "nginx-http-auth", "recidive"],
  "jail_count": 3,
  "banned_ips": 12
}
```

### System updates (read-only)

Counts pending packages via `apt-check` / `apt list --upgradable` / `dnf`/`yum`. Never installs packages.

```json
{
  "available": 17,
  "security": 4,
  "manager": "apt",
  "reboot_required": false
}
```

Risk finding example:

- **12 security updates pending** → MEDIUM (`SECURITY_UPDATES_PENDING`)
- Non-security updates only → LOW (`UPDATES_AVAILABLE`)
- Reboot required flag → LOW (`REBOOT_REQUIRED`)

### Also collected

- **Processes** — top CPU consumers, count
- **System** — hostname, OS, kernel, architecture

## What not to do

- Do not SSH from the Sandbox backend into customer servers.
- Do not put a permanent `sba_…` credential in the install command or chat logs.
- Do not share one credential across servers. Revoke is per server.
- Do not send a user JWT to register or ingest.
- Do not give the agent a command channel, remote shell, or write access to firewall/SSH/packages. See [../../agent/SECURITY.md](../../agent/SECURITY.md).
