# Backup strategy

**Status:** Production Compose includes an automated **backup service** (`infrastructure/backup/`) that runs scheduled dumps, encrypted storage on a separate volume, retention, and monthly restore verification.

This document defines:

1. **In-repo automation** (scripts, schedule, retention, restore, restore test)
2. Data classification (Postgres, reports, config, Redis)
3. Operator procedures for disaster recovery

If the volume or database is lost and you have no backups, **tenant data is gone**.

---

## Automated backup service (production Compose)

```
PostgreSQL (postgres_data volume)
        │
        ▼
  backup service (cron)
        │
        ├── pg_dump -Fc → gzip → AES-256 (openssl)
        ├── optional report volume tar
        ├── retention (default 7 days)
        └── optional S3 upload (BACKUP_S3_URI)
        │
        ▼
backup_storage volume (/backups)   ← separate from postgres_data
```

| Schedule | Job | Script |
|----------|-----|--------|
| Daily 02:00 UTC | Postgres (+ optional reports) backup | `backup.sh` |
| Monthly 1st 03:00 UTC | Restore verification | `restore-test.sh` |

### Quick commands

```bash
# One-off backup (prod stack must be running)
make backup-now

# Monthly restore test (creates sandbox_restore_test DB, verifies, drops it)
make backup-restore-test

# Disaster recovery — stop writers first, then:
docker compose -f docker-compose.prod.yml stop backend celery-worker celery-beat
make backup-restore FILE=postgres/sandbox-YYYYMMDD-HHMMSS.dump.enc
docker compose -f docker-compose.prod.yml start backend celery-worker celery-beat

# Required CI quality-gate job (ephemeral stack)
make backup-integration-test
```

Artifacts live under the **`backup_storage`** named volume:

| Path | Content |
|------|---------|
| `/backups/postgres/sandbox-*.dump.enc` | Encrypted Postgres dumps |
| `/backups/reports/reports-*.tar.gz.enc` | Encrypted report files (when `BACKUP_REPORT_FILES=true`) |
| `/backups/logs/*.json` | Backup manifests (sha256, size) |
| `/backups/restore-tests/*.json` | Restore test results |

Copy the volume offsite or set `BACKUP_S3_URI` for object storage sync.

### Configuration

See [configuration.md](./configuration.md) and `.env.production.example`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKUP_ENCRYPTION_PASSPHRASE` | — | **Required in production** — AES-256 encryption |
| `BACKUP_RETENTION_DAYS` | `7` | Delete local artifacts older than N days |
| `BACKUP_REPORT_FILES` | `true` | Include report volume in daily backup |
| `BACKUP_S3_URI` | empty | Optional `s3://bucket/prefix` offsite copy |

Generate passphrase: `openssl rand -hex 32`

---

## Data classification

| Asset | Is it durable business data? | Backup required? | Notes |
|-------|------------------------------|------------------|-------|
| **PostgreSQL** | **Yes — source of truth** | **Yes** | Users, orgs, assets, scans, findings, risk, audit logs, AI conversations, report *metadata* |
| **Report PDF/HTML files** | Derived artifacts | **Yes (recommended)** | Stored via `ReportStorageBackend`: Compose volume `report_storage` (local) or S3 bucket (`REPORT_STORAGE_BACKEND=s3`). Metadata + `file_url` key in Postgres. Regeneratable from findings if lost. |
| **Uploaded user files** | **N/A in V1** | N/A | There is **no** file-upload product. Org logos are `logo_url` strings (external URLs), not stored blobs |
| **Configuration (`.env`)** | Operational secrets | **Yes** (secret vault) | Not in git; not recoverable from Postgres |
| **Redis** | **No — ephemeral** | **No** | Broker, rate limits, lockout counters only — see [Redis](#redis-ephemeral-not-business-data) |
| **Grafana / Prometheus / Loki volumes** | Observability only | Optional | Can rebuild; not tenant security data |
| **Application code** | Source | Git remote | Not part of DB backup |

---

## PostgreSQL policy

| Dimension | Default (in-repo) |
|-----------|-------------------|
| **Frequency** | Daily 02:00 UTC (cron in backup service) |
| **Retention** | 7 days (`BACKUP_RETENTION_DAYS`) |
| **Storage** | Encrypted on `backup_storage` volume; optional S3 |
| **Restore test** | Required CI job + monthly cron + `make backup-integration-test` / `tests/test_backup_restore.py` |
| **Before migrations** | Run `make backup-now` before `alembic upgrade head` on production |

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

### Managed Postgres (RDS, Cloud SQL)

Use provider automated backups + PITR if available. Still run **monthly restore verification** into a staging database.

---

## Reports

| Item | Behavior |
|------|----------|
| **Metadata** | PostgreSQL `reports` table |
| **File bytes** | `ReportStorageBackend` — see [reports/storage.md](../reports/storage.md) |
| **Automated backup** | Daily tar of `report_storage` when `BACKUP_REPORT_FILES=true` |
| **Cloud** | Prefer `REPORT_STORAGE_BACKEND=s3` with versioning / replication |

---

## Uploaded files

**V1 has no uploaded-file store.** Organization branding uses `organizations.logo_url` (URL string), not local blobs.

---

## Configuration

| Item | Backup / recovery |
|------|-------------------|
| `.env` | **Critical.** Store in a secret manager. Includes `BACKUP_ENCRYPTION_PASSPHRASE` |
| Compose / nginx / Grafana | In **git** |
| Alembic migrations | In **git** under `backend/alembic/versions/` |

After restoring a database dump, you still need app secrets. Rotating `JWT_SECRET` invalidates sessions — expected.

---

## Redis (ephemeral — not business data)

**Do not treat Redis as persistent business data.**

Postgres remains the authority. Redis is **not** included in backup jobs. After disaster recovery: start Redis empty, start workers.

---

## Restore process

1. **Stop writers** — `backend`, `celery-worker`, `celery-beat`
2. **Restore PostgreSQL** — `make backup-restore FILE=postgres/sandbox-....dump.enc` (uses `--drop-first`)
3. **Confirm schema** — `docker compose exec backend alembic current`
4. **Restore report files** (optional) — decrypt reports backup or reattach S3/volume
5. **Restore configuration** from secret manager
6. **Start Redis empty**
7. **Start app and workers**; hit `/health/ready`
8. **Smoke test** — login, list assets, download a report
9. **Record** restore time, dump ID, outcome

### Monthly restore test

The backup service runs `restore-test.sh` on the 1st of each month. It:

1. Takes a fresh backup
2. Restores into `sandbox_restore_test`
3. Verifies row counts for `users` and `organizations`
4. Drops the test database
5. Writes JSON result to `/backups/restore-tests/`

Run manually: `make backup-restore-test` or `make backup-integration-test` (ephemeral CI stack).

**Untested backups are not a recovery plan.**

---

## Manual procedures (without backup service)

If you run Postgres outside Compose, use the same scripts from `infrastructure/backup/scripts/` with `POSTGRES_*` and `BACKUP_ROOT` set.

```bash
# Custom format dump (same as backup.sh internals)
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sandbox}" \
  -d "${POSTGRES_DB:-sandbox}" \
  -Fc > "sandbox-$(date +%Y%m%d-%H%M%S).dump"
```

Encrypt with `BACKUP_ENCRYPTION_PASSPHRASE` and openssl as in `backup.sh`.

### Dangerous Compose command

`docker compose down -v` **deletes named volumes** including `postgres_data` and `backup_storage`. Never use `-v` without a verified recent backup.

---

## Implementation reference

| Component | Location |
|-----------|----------|
| Backup image + cron | `infrastructure/backup/` |
| Prod service | `docker-compose.prod.yml` → `backup` |
| Integration stack | `docker-compose.backup-test.yml` |
| Restore test (pytest) | `backend/tests/test_backup_restore.py` |
| Makefile targets | `backup-now`, `backup-restore`, `backup-restore-test`, `backup-integration-test` |

---

## Related

- [installation.md](./installation.md) — first-time Compose bring-up
- [production.md](./production.md) — production checklist
- [configuration.md](./configuration.md) — secrets and env vars
- [database/migrations.md](../database/migrations.md) — dump before upgrades
