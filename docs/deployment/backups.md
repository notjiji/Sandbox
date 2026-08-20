# Backups

**There is no automated backup job in this repository.** Postgres data lives in a Docker named volume. If the volume is deleted or the host disk fails, **data is lost** unless you maintain backups outside this codebase.

This document describes what to protect and how operators can back up and restore manually.

## What needs protection

| Asset | Location | Criticality |
|-------|----------|-------------|
| PostgreSQL database | Docker volume `postgres_data` | **Critical** — all tenants, users, scans, findings, audit logs |
| Generated PDF reports | `backend/storage/reports/` (bind mount in dev Compose) | High — can be regenerated but costly |
| Redis | Volume `redis_data` | Medium — mostly Celery queue state; usually rebuildable |
| Grafana dashboards | Volume `grafana_data` | Low — reprovisioned from `infrastructure/monitoring/grafana` |
| Prometheus / Loki | Volumes `prometheus_data`, `loki_data` | Low — operational telemetry |
| Environment secrets | `.env` file (not in git) | **Critical** — store separately in secret manager |
| Application code | Git repository | Recoverable from remote |

Audit logs are in Postgres with hash-chain integrity per organization. Backup Postgres **before** major upgrades or migrations.

## Backup strategy (operator-defined)

Recommended minimum for any non-demo deployment:

1. **Daily logical backup** of Postgres (`pg_dump`)
2. **Encrypted offsite copy** of dumps (S3, another region, tape — your policy)
3. **Test restore quarterly** on a non-production instance
4. **Version control** for `.env` secrets in a vault, not in backup archives unencrypted

Retention, encryption, and RPO/RTO targets are **your** policy — not specified by Sandbox NFRs beyond documenting the gap ([NFR-AVL-14](../product/non-functional-requirements.md)).

## Manual Postgres backup (Compose)

While the stack is running:

```bash
# Custom format (recommended for pg_restore)
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sandbox}" \
  -d "${POSTGRES_DB:-sandbox}" \
  -Fc \
  > "sandbox-$(date +%Y%m%d-%H%M%S).dump"

# Plain SQL (human-readable, larger)
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sandbox}" \
  -d "${POSTGRES_DB:-sandbox}" \
  > "sandbox-$(date +%Y%m%d-%H%M%S).sql"
```

Use credentials from your `.env`. Store dumps encrypted at rest.

### Backup report files

```bash
tar -czf sandbox-reports-$(date +%Y%m%d).tar.gz -C backend storage/reports
```

## Manual Postgres restore

**Warning:** restore overwrites data in the target database. Stop application traffic first.

```bash
# Stop writers (optional but recommended)
docker compose stop backend celery-worker celery-beat

# Drop and recreate DB (destructive)
docker compose exec postgres psql -U sandbox -c "DROP DATABASE IF EXISTS sandbox;"
docker compose exec postgres psql -U sandbox -c "CREATE DATABASE sandbox;"

# Restore from custom format
docker compose exec -T postgres pg_restore \
  -U sandbox \
  -d sandbox \
  --no-owner --no-acl \
  < sandbox-YYYYMMDD-HHMMSS.dump

# Or from plain SQL
docker compose exec -T postgres psql -U sandbox -d sandbox < sandbox-YYYYMMDD-HHMMSS.sql

# Restart app
docker compose start backend celery-worker celery-beat
```

After restore, confirm Alembic revision matches expectations:

```bash
docker compose exec backend alembic current
```

If restore is from an older dump, run `alembic upgrade head` only after verifying schema compatibility.

## Volume-level backup (whole data directory)

Alternative to logical dump — copy the entire Postgres volume while **Postgres is stopped**:

```bash
docker compose stop postgres
docker run --rm \
  -v sandbox_postgres_data:/data \
  -v "$(pwd)/backups":/backup \
  alpine tar czf /backup/postgres_data-$(date +%Y%m%d).tar.gz -C /data .
docker compose start postgres
```

Volume name may be prefixed with project name (`sandbox_postgres_data`). List with `docker volume ls`.

Volume snapshots require consistent filesystem state — prefer `pg_dump` for live backups.

## Redis

Redis holds Celery task queues. For disaster recovery, flushing and re-queuing failed jobs is usually acceptable. Optional:

```bash
docker compose exec redis redis-cli SAVE
docker cp "$(docker compose ps -q redis)":/data/dump.rdb ./redis-backup.rdb
```

## What is not backed up by Compose

- `docker compose down -v` **deletes named volumes** — never use `-v` on production unless intentional
- Migrations are in git (`backend/alembic/versions/`), not in the database backup alone
- Audit immutability triggers exist in Postgres only — restored dumps on SQLite test DBs do not include triggers

## Future work

Automated backup jobs, PITR, and restore verification are listed as **not implemented** in [roadmap/known-limitations.md](../roadmap/known-limitations.md). Until then, treat manual procedures in this document as the operator runbook.

Related: [installation.md](./installation.md), [production.md](./production.md), [database/migrations.md](../database/migrations.md).
