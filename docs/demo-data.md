# Demo Data — Sandbox

One command populates a full demo tenant for sales demos, QA, and onboarding.

```bash
make migrate   # if not already applied
make seed
```

Or directly:

```bash
docker compose exec backend python scripts/seed_demo.py
```

---

## Login credentials

**All demo accounts share the same password:**

| Field | Value |
|-------|-------|
| **Password** | `DemoPassword1!` |

| Email | Role | Name | Best for testing |
|-------|------|------|------------------|
| `owner@demo.sandbox` | Owner | Alex Owner | Full access, org settings, member management |
| `admin@demo.sandbox` | Admin | Casey Admin | Day-to-day admin without ownership transfer |
| `analyst@demo.sandbox` | Security Analyst | Sam Analyst | Scans, findings, risk review |
| `manager@demo.sandbox` | Manager | Morgan Manager | Projects and reporting |
| `viewer@demo.sandbox` | Viewer | Riley Viewer | Read-only access |

Emails are pre-verified — no OTP step required.

---

## Organization

| Field | Value |
|-------|-------|
| Name | Demo Corp |
| Slug | `demo-corp` |
| Website | https://demo-corp.com |

After login, select **Demo Corp** on the organization picker (or it auto-selects if it is your only org).

---

## Projects

### 1. Production Web Apps (`production-web`)

Customer-facing websites and APIs. This is the main project to explore.

| Asset | Type | Scan status | Notes |
|-------|------|-------------|-------|
| Demo Corp Website | website | Completed (full scan) | 5 open findings, risk score calculated |
| demo-corp.com | domain | — | Root DNS asset |
| Website Public IP | public_ip | — | Child of website |
| Public API Gateway | api_endpoint | Completed (quick scan) | 2 open findings |
| Legacy App Server | server | Queued (not run) | **Unscanned** — shows null risk score in UI |

### 2. Cloud Infrastructure (`cloud-infra`)

| Asset | Type | Scan status |
|-------|------|-------------|
| AWS Production | cloud_account | Not scanned |
| Application Logs Bucket | s3_bucket | Not scanned |

---

## Scans & findings

### Completed scans

1. **Demo Corp Website** — Full scan  
   Findings: Missing CSP, Missing HSTS, Expired SSL, Missing SPF, Domain expiring soon

2. **Public API Gateway** — Quick scan  
   Findings: Missing HSTS, TLS 1.0 enabled

### Pending scan

- **Legacy App Server** — status `queued` (never completed), useful for scan lifecycle UI

### Sample finding codes (from risk rules)

| Code | Severity | Score |
|------|----------|-------|
| `SSL_EXPIRED` | critical | 50 |
| `PORT_TELNET_OPEN` | critical | 45 |
| `SSL_TLS10_ENABLED` | high | 30 |
| `HTTP_NO_HSTS` | high | 25 |
| `HTTP_NO_CSP` | medium | 15 |
| `DNS_MISSING_SPF` | medium | 10 |
| `WHOIS_EXPIRING_SOON` | low | 5 |

---

## Suggested walkthrough

1. **Login** as `owner@demo.sandbox` / `DemoPassword1!`
2. **Dashboard** — org-level risk (averages scanned assets only)
3. **Projects → Production Web Apps** — project risk score and grade
4. **Assets** — open Demo Corp Website vs Legacy App Server (scanned vs unscanned)
5. **Scans** — completed full/quick scans + queued scan on legacy server
6. **Findings** — 7 open findings across the project
7. **Logout**, login as `viewer@demo.sandbox` — confirm read-only behavior

---

## Re-seeding

The seed script is idempotent: if `demo-corp` already exists, it skips and prints credentials.

To start fresh:

```bash
docker compose down -v
docker compose up -d
make migrate
make seed
```

---

## Local development (no Docker)

From `backend/` with `.env` configured:

```bash
alembic upgrade head
python scripts/seed_demo.py
```

Frontend: http://localhost:5173  
API: http://localhost:8000/api/v1
