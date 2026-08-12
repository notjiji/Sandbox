# Monitoring API

User routes require a session, `X-Organization-ID`, and the listed permission. Register and ingest are **not** user-JWT routes.

## Asset routes

Base: `/api/v1/projects/{projectId}/assets/{assetId}/monitoring`

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/` | `monitoring:read` | Latest metrics, security checks, alerts, history |
| `POST` | `/enroll` | `monitoring:manage` | Issue a short-lived enrollment token and install command |
| `POST` | `/revoke` | `monitoring:manage` | Destroy this server's credential only |

`GET ?hours=24` (1–168).

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
| `POST` | `/api/v1/monitoring/ingest` | `Authorization: Bearer sba_…` | Heartbeat |

Register body:

```json
{ "enrollment_token": "sbe_...", "hostname": "vps-01", "agent_version": "1.0.0" }
```

Register returns `{ "credential": "sba_...", "agent_id", "asset_id" }`. The enrollment token cannot be reused and cannot call ingest.

## Organization route

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/organizations/current/monitoring/overview` | `monitoring:read` |

## Permissions

| Role | Read | Install / revoke |
|------|:----:|:----------------:|
| owner, admin, security_analyst | ✓ | ✓ |
| manager, viewer | ✓ | — |
