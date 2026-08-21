# Backup strategy

**Status:** This repository does **not** ship an automated backup job, PITR, or scheduled restore test. Operators must implement the policy below on their deployment target (Compose host, managed Postgres, Kubernetes, cloud DB, etc.).

This document defines:

1. A **recommended policy** for PostgreSQL (frequency, retention, storage, restore)
2. What happens to **reports**, **uploaded files**, **configuration**, and **Redis**
3. Manual procedures for Compose-based deployments

If the volume or database is lost and you have no backups, **tenant data is gone**.

---

## Data classification

| Asset | Is it durable business data? | Backup required? | Notes |
|-------|------------------------------|------------------|-------|
| **PostgreSQL** | **Yes — source of truth** | **Yes** | Users, orgs, assets, scans, findings, risk, audit logs, AI conversations, report *metadata* |
| **Report PDF/HTML files** | Derived artifacts | Recommended | On disk under `backend/storage/reports/`; can be regenerated from DB + findings |
| **Uploaded user files** | **N/A in V1** | N/A | There is **no** file-upload product. Org logos are `logo_url` strings (external URLs), not stored blobs |
| **Configuration (`.env`)** | Operational secrets | **Yes** (secret vault) | Not in git; not recoverable from Postgres |
| **Redis** | **No — ephemeral** | **No** | Broker, rate limits, lockout counters only — see [Redis](#redis-ephemeral-not-business-data) |
| **Grafana / Prometheus / Loki volumes** | Observability only | Optional | Can rebuild; not tenant security data |
| **Application code** | Source | Git remote | Not part of DB backup |

---

## PostgreSQL policy (recommended)

The exact tooling depends on your deployment target (self-hosted Compose, RDS, Cloud SQL, etc.). The **policy intent** should be at least:

| Dimension | Recommended default |
|-----------|---------------------|
| **Frequency** | **Daily** full logical backup (or continuous WAL / PITR if using managed Postgres) |
| **Retention** | **7 days** of daily dumps (extend for regulated environments) |
| **Storage location** | **Encrypted** offsite object storage (e.g. S3/GCS/Azure Blob with SSE / customer-managed keys), **not** only the application host |
| **Restore process** | Documented restore to a staging database; **test restoration monthly** |
| **Before migrations** | Take an extra on-demand dump before `alembic upgrade head` on production |

### Example policy (copy into your runbook)

```
Daily backup
7-day retention
Encrypted storage (offsite)
Test restoration monthly
```

### What a Postgres backup must include

Everything in the application database, including:

- Auth and membership (`users`, tokens, org members)
- Inventory (`projects`, `assets`, metadata, tags)
- Scan history and plugin runs
- Findings and risk snapshots / history
- Report rows (status, type, paths referenced) — **not** the PDF bytes themselves
- Audit logs (`audit_logs` with `prev_hash` / `entry_hash` chain)
- AI conversation history
- Monitoring enrollments and metrics history

Audit hash chains are **per organization** and live only in Postgres. Losing the DB loses the chain; restoring a dump restores it as of that dump.

### Deployment-target notes

| Target | Typical approach |
|--------|------------------|
| Docker Compose (this repo) | Cron on the host: `pg_dump` → encrypt → upload to object storage (see [Manual procedures](#manual-procedures-compose)) |
| Managed Postgres (RDS, Cloud SQL, Azure DB) | Use provider automated backups + PITR; still verify restore monthly |
| Kubernetes | Volume snapshots **or** logical dump CronJob; prefer logical dumps for portability across clusters |

---

## Reports

| Item | Behavior |
|------|----------|
| **Where files live** | `backend/storage/reports/{report_id}.pdf` and `.html` (see `app/core/report_engine/renderer.py`) |
| **In Compose** | Backend bind-mounts `./backend:/app`, so files sit on the host under `backend/storage/reports/` |
| **In the database** | Report metadata/status; download APIs read files from disk |
| **If files are lost** | Metadata may still show `ready`, but download fails until regenerated |
| **Backup recommendation** | Include `storage/reports/` in daily backup **or** accept regeneration after restore |

Reports are **not** the system of record for findings. Prefer Postgres integrity first; back up report files if customers expect historical PDF downloads without re-running generation.

```bash
tar -czf sandbox-reports-$(date +%Y%m%d).tar.gz -C backend storage/reports
# Encrypt and ship offsite with the same retention as DB dumps
```

---

## Uploaded files

**V1 has no uploaded-file store.**

- Organization branding uses `organizations.logo_url` (URL string), not a multipart upload to local disk.
- There is no `uploads/` product directory for tenant media.

Do not invent a backup path for “user uploads” unless you add an upload feature later. If you later store blobs on disk or object storage, extend this document with that path and retention.

---

## Configuration

| Item | Backup / recovery |
|------|-------------------|
| `.env` | **Critical.** Store in a secret manager (or encrypted vault). Never rely on Postgres to recover `SECRET_KEY`, `JWT_SECRET`, DB password, Resend, OpenAI, SIEM tokens |
| `docker-compose.yml`, nginx, Grafana provisioning | In **git** — restore by cloning the repo |
| Alembic migrations | In **git** under `backend/alembic/versions/` |

After restoring a database dump to a new environment, you still need the **same** (or intentionally rotated) app secrets. Rotating `JWT_SECRET` invalidates all sessions — that is expected, not a restore failure.

---

## Redis (ephemeral — not business data)

**Do not treat Redis as persistent business data.**

In this product Redis is used for:

| Use | Durable? | On Redis loss |
|-----|----------|---------------|
| Celery broker / result backend | No | In-flight and queued jobs are lost; re-run scans/reports |
| API rate-limit counters (SlowAPI) | No | Counters reset; temporary higher burst until limits refill |
| Account lockout counters | No | Active lockouts clear; users can retry login |

Postgres remains the authority for users, memberships, assets, findings, and audit. Redis is **not** a replica of tenant data ([NFR-AVL-12](../product/non-functional-requirements.md)).

Compose mounts volume `redis_data` for Redis persistence of its own RDB — that is for **operational convenience**, not a backup strategy for Sandbox. Operators may discard Redis volumes freely after confirming Celery queues can be empty.

**Recommended policy:** do **not** include Redis dumps in the 7-day encrypted backup set. After disaster recovery: start Redis empty, start workers, let the app recreate ephemeral keys.

---

## Restore process (policy)

1. **Stop writers** — stop `backend`, `celery-worker`, `celery-beat` (or take traffic off the load balancer).
2. **Restore PostgreSQL** from the chosen daily dump (or PITR to a point in time).
3. **Confirm schema** — `alembic current` matches the dump era; upgrade only if intentional.
4. **Restore report files** (optional) into `backend/storage/reports/` if you backed them up.
5. **Restore configuration** from secret manager into `.env` / runtime secrets.
6. **Start Redis empty** (or existing empty volume) — do not require a Redis dump.
7. **Start app and workers**; hit `/health/ready`.
8. **Smoke test** — login, open an org, list assets, download a known report if files were restored.
9. **Record** restore time, dump ID, and outcome (required for the monthly restore test).

### Monthly restore test

At least once per month:

- Restore the latest daily dump into a **non-production** database
- Verify row counts / login / one asset / one finding
- Document pass/fail

Untested backups are not a recovery plan.

---

## Manual procedures (Compose)

### Daily Postgres dump

```bash
# Custom format (recommended for pg_restore)
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sandbox}" \
  -d "${POSTGRES_DB:-sandbox}" \
  -Fc \
  > "sandbox-$(date +%Y%m%d-%H%M%S).dump"
```

Then encrypt and upload offsite (example with age or gpg — choose your tool):

```bash
# Example only — replace with your KMS / object-storage pipeline
gpg --symmetric --cipher-algo AES256 "sandbox-YYYYMMDD-HHMMSS.dump"
# Upload .gpg to encrypted bucket; delete local plaintext when safe
```

Retention job: delete encrypted dumps older than **7 days** in that bucket (lifecycle rule preferred over ad-hoc scripts).

### Restore Postgres

```bash
docker compose stop backend celery-worker celery-beat

docker compose exec postgres psql -U sandbox -c "DROP DATABASE IF EXISTS sandbox;"
docker compose exec postgres psql -U sandbox -c "CREATE DATABASE sandbox;"

# After decrypting the dump locally:
docker compose exec -T postgres pg_restore \
  -U sandbox \
  -d sandbox \
  --no-owner --no-acl \
  < sandbox-YYYYMMDD-HHMMSS.dump

docker compose start backend celery-worker celery-beat
docker compose exec backend alembic current
```

### Dangerous Compose command

`docker compose down -v` **deletes named volumes** including `postgres_data`. Never use `-v` on a deployment that lacks a verified recent backup.

---

## What this repo does not automate

| Capability | In-repo? |
|------------|----------|
| Scheduled `pg_dump` | No |
| Encrypted offsite upload | No |
| Lifecycle / 7-day retention job | No |
| Monthly restore CI | No |
| WAL archiving / PITR | No |
| Redis as durable store | No (by design) |

Until those exist as product features, this document is the operator runbook. Related limitation: [NFR-AVL-14](../product/non-functional-requirements.md), [roadmap/known-limitations.md](../roadmap/known-limitations.md).

---

## Related

- [installation.md](./installation.md) — first-time Compose bring-up
- [production.md](./production.md) — production checklist (includes backups)
- [configuration.md](./configuration.md) — secrets and env vars
- [database/migrations.md](../database/migrations.md) — Alembic; dump before upgrades
