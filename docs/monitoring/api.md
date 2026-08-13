# Monitoring API

User routes require a session, `X-Organization-ID`, and the listed permission. Register and ingest are **not** user-JWT routes.

## Asset routes

Base: `/api/v1/projects/{projectId}/assets/{assetId}/monitoring`

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/` | `monitoring:read` | Latest metrics, security checks, alerts, history |
| `GET` | `/metrics` | `monitoring:read` | Time-series for CPU, RAM, disk, load, network (`?hours=24`) |
| `POST` | `/enroll` | `monitoring:manage` | Issue a short-lived enrollment token and install command |
| `POST` | `/revoke` | `monitoring:manage` | Destroy this server's credential only |

`GET ?hours=24` (1–168).

The asset **is** the server. Conceptual routes map as:

| Concept | This API |
|---------|----------|
| `POST/GET /servers` | Asset create/list (`type=server`) |
| `GET /servers/{id}` | Asset + `GET .../monitoring` |
| `POST /servers/{id}/agent/enrollment` | `POST .../monitoring/enroll` |
| `POST /agents/register` | `POST /api/v1/monitoring/register` |
| `POST /agents/heartbeat` + metrics | `POST /api/v1/monitoring/ingest` (one call) |
| `GET /servers/{id}/metrics` | `GET .../monitoring/metrics` |
| `GET /servers/{id}/services` | Overview `metrics.services` |
| `GET /servers/{id}/security` | Overview `security` |
| `GET /servers/{id}/alerts` | Overview `alerts` |

Enrollment response:

- `enrollment_token` (`sbe_…`) — shown once, expires in 15 minutes, single-use
- `install_command` — `curl …/install.sh \| sudo env … bash`
- `python_command` — local/dev fallback
- `expires_at`

Re-enrolling issues a **new enrollment token**. The existing per-server credential keeps working until the new agent registers and replaces it.

## Agent routes (no user JWT, no org header)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/monitoring/install.sh` | none | Bootstrap script |
| `POST` | `/api/v1/monitoring/register` | enrollment token in body | Exchange `sbe_…` for `sba_…` credential |
| `POST` | `/api/v1/monitoring/ingest` | `Authorization: Bearer sba_…` | Heartbeat + metrics |

Register body:

```json
{ "enrollment_token": "sbe_...", "hostname": "vps-01", "agent_version": "1.0.0" }
```

Register returns `{ "credential": "sba_...", "agent_id", "asset_id" }`. The enrollment token cannot be reused and cannot call ingest.

## Organization route

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/organizations/current/monitoring/overview` | `monitoring:read` |

Each server includes `cpu_percent`, `ram_percent`, `disk_percent`, `uptime_seconds`, and a compact `security` summary (`ok` / `warn` / `unknown` for SSH, firewall, Fail2Ban, updates, Docker). The dashboard **Servers** section uses this payload. Clicking a card opens `/projects/{projectId}/assets/{assetId}/monitoring`.

## Permissions

| Role | Read | Install / revoke |
|------|:----:|:----------------:|
| owner, admin, security_analyst | ✓ | ✓ |
| manager, viewer | ✓ | — |
