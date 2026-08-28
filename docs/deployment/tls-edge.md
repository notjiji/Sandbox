# TLS and public edge deployment

Single-server v1 uses **Caddy** in front of the existing app nginx. Caddy terminates HTTPS on `:443`, obtains Let's Encrypt certificates automatically, and forwards plain HTTP to nginx on the internal Docker network.

```
User
 │  HTTPS :443
 ▼
Caddy (TLS termination, ACME, HTTP→HTTPS redirect)
 │
 │  HTTP (internal)
 ▼
Nginx
 ├── /        → React (static frontend container)
 └── /api/*   → FastAPI (backend container)
```

Postgres, Redis, Celery, and backups stay on the **internal** network with no public ports.

---

## Quick start (production)

1. Copy and edit env:

```bash
cp .env.production.example .env
```

Set at minimum:

| Variable | Example |
|----------|---------|
| `EDGE_DOMAIN` | `app.example.com` |
| `ACME_EMAIL` | `ops@example.com` |
| `FRONTEND_URL` | `https://app.example.com` |
| `PUBLIC_API_URL` | `https://app.example.com/api/v1` |
| `CORS_ORIGINS` | `https://app.example.com` |

2. DNS must point `EDGE_DOMAIN` to this server's public IP **before** first boot (Let's Encrypt HTTP-01).

3. Firewall: allow **80** and **443** inbound; block Postgres/Redis/Grafana from the internet.

4. Deploy with the edge overlay:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.edge.yml run --rm migrate
docker compose -f docker-compose.prod.yml -f docker-compose.edge.yml up -d --build
```

Or: `make prod-edge-up` after `make prod-edge-migrate`.

5. Verify:

```bash
curl -I https://app.example.com
curl -I https://app.example.com/api/v1/health
```

---

## Compose files

| File | Role |
|------|------|
| `docker-compose.prod.yml` | App stack; nginx on internal `:80` (optional host bind via `NGINX_HTTP_PORT`) |
| `docker-compose.edge.yml` | Adds Caddy; removes nginx host port; publishes `443`/`80` |

Without the edge overlay, nginx remains the HTTP entry (local/staging only). Production URLs in `.env` still require **HTTPS** — use the edge overlay or your own TLS proxy.

---

## Staging without public DNS

Use Caddy's internal CA (browser will warn):

```bash
# in .env
CADDYFILE=./infrastructure/edge/Caddyfile.internal
EDGE_DOMAIN=localhost
FRONTEND_URL=https://localhost
PUBLIC_API_URL=https://localhost/api/v1
CORS_ORIGINS=https://localhost
```

Then start with the edge overlay. Accept the self-signed certificate in the browser.

---

## Bring your own TLS proxy

If you prefer Traefik, nginx on the host, or a cloud load balancer, **do not** use `docker-compose.edge.yml`. Instead:

1. Bind nginx to localhost only:

```bash
NGINX_HTTP_PORT=127.0.0.1:8080
```

2. Terminate TLS at your proxy and forward HTTP to `127.0.0.1:8080`.

3. Set these headers on every request:

| Header | Value |
|--------|-------|
| `Host` | Public hostname |
| `X-Forwarded-Proto` | `https` |
| `X-Forwarded-For` | Client IP chain |
| `X-Real-IP` | Client IP (optional) |

App nginx preserves `X-Forwarded-Proto` when forwarding to FastAPI (see `infrastructure/nginx/nginx.prod.conf`).

---

## Configuration reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `EDGE_DOMAIN` | — | Public hostname for Caddy site block and ACME |
| `ACME_EMAIL` | — | Let's Encrypt account email |
| `EDGE_HTTP_PORT` | `80` | Host port for HTTP (ACME + redirect) |
| `EDGE_HTTPS_PORT` | `443` | Host port for HTTPS |
| `CADDYFILE` | `./infrastructure/edge/Caddyfile` | Override for staging (`Caddyfile.internal`) |
| `NGINX_HTTP_PORT` | `80` | Host bind when **not** using edge overlay |

Certificate storage: Docker volumes `caddy_data` and `caddy_config` (persist across container restarts).

---

## Operations

### Renewals

Caddy renews certificates automatically. Check logs:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.edge.yml logs -f caddy
```

### Restart edge only

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.edge.yml restart caddy
```

App containers keep running; brief TLS interruption only.

### Validate Caddy config

```bash
bash scripts/ci/validate-edge.sh
```

---

## Security notes

- Only Caddy (or your external proxy) should be reachable on 443 from the internet.
- `/metrics`, `/docs`, `/redoc`, and `/openapi.json` remain blocked at app nginx on the public path.
- Production startup validator requires HTTPS in `FRONTEND_URL`, `PUBLIC_API_URL`, and `CORS_ORIGINS` — match your `EDGE_DOMAIN`.

Related: [production.md](./production.md), [production-runbook.md](./production-runbook.md), [configuration.md](./configuration.md).
