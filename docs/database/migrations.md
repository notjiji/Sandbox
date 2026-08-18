# Migrations

- Tool: Alembic (`backend/alembic/`). Config: `backend/alembic.ini`.
- Apply in Compose: `make migrate` → `docker compose exec backend alembic upgrade head`.
- Down one: `make migrate-down`.
- Linear revisions `001` … `045_audit_log_hash_chain`.
- **044** adds `audit_logs.severity`.
- **045** adds `prev_hash` / `entry_hash` and trigger `audit_logs_immutable`.
- Hash chains are **per organization**. Integrity verification **skips** rows with NULL `entry_hash` (pre-045 / legacy).

## Environments

| Environment | Schema |
|-------------|--------|
| Docker Postgres | Alembic. **Must** be at head for hash-chain and delayed agent status. |
| Pytest | Typically SQLite + `create_all` from models. **No** Postgres immutability trigger. Hash-chain verify tests that need hashes create them in-app. |

## Operational notes

- There is **no** automated backup migration or dump job in this repo.
- Destructive downgrades are manual (`migrate-down`); not used in the default deploy path.
- Seed data (`make seed`) assumes migrations are already at head.
