# Database

Postgres 16 in Compose. SQLAlchemy models in feature modules. Migrations: Alembic, current head **`045_audit_log_hash_chain`**.

| Document | Covers |
|----------|--------|
| [ER diagram](./erd.md) | Logical spine + mermaid ERD + cardinalities from model FKs (**33 tables**) |
| [Tables](./tables.md) | Table list and important columns |
| [Migrations](./migrations.md) | How schema is applied; SQLite tests |

The ERD is generated from SQLAlchemy metadata (`ForeignKey`, unique constraints, nullability). There is no checked-in PNG.
