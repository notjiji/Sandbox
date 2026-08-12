# Monitoring API

All user routes require a session, `X-Organization-ID`, and the listed permission. The ingest route is **agent-token only**.

## Asset routes

Base: `/api/v1/projects/{projectId}/assets/{assetId}/monitoring`

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/` | `monitoring:read` | Latest metrics, security checks, alerts, history |
| `POST` | `/enroll` | `monitoring:manage` | Create or rotate the agent token (plaintext returned once) |
| `POST` | `/revoke` | `monitoring:manage` | Invalidate the current token |

Query: `GET ?hours=24` (1–168).

Enrollment response includes `token`, `api_url`, and `install_command`. Re-enrolling rotates the token and sets status back to `pending` until the next heartbeat.

## Organization route

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/api/v1/organizations/current/monitoring/overview` | `monitoring:read` | Online/offline/pending counts, open alerts, per-server snapshot |

## Agent ingest

`POST /api/v1/monitoring/ingest`

```
Authorization: Bearer sba_...
Content-Type: application/json
```

Do **not** send a user JWT or `X-Organization-ID`. The token identifies the organization, project, and asset.

Body (abridged):

```json
{
  "hostname": "vps-01",
  "agent_version": "1.0.0",
  "metrics": { "cpu_percent": 12.4, "ram_percent": 41.0, "disk_percent": 55.2 },
  "security": {
    "firewall": { "enabled": true, "backend": "ufw" },
    "ssh": { "permit_root_login": false, "password_authentication": false }
  }
}
```

Unknown fields are ignored so older and newer agents stay compatible.

## Permissions

| Role | Read | Enroll / revoke |
|------|:----:|:---------------:|
| owner, admin, security_analyst | ✓ | ✓ |
| manager, viewer | ✓ | — |

## Isolation

Agents and snapshots are organization-scoped. Cross-org access to another tenant's asset monitoring returns 404/403. A revoked or unknown token returns 401.
