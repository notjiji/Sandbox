# Deployment

Local Compose is the documented runtime. There is no in-repo Kubernetes/Helm chart or managed backup.

| Document | Covers |
|----------|--------|
| [Local setup](./local.md) | `make up` / migrate / seed |
| [Docker Compose](./docker.md) | Services |
| [Environment](./environment.md) | Variables from `config.py` / `.env.example` |
| [Health](./health.md) | Probes |
| [Production](./production.md) | What the settings validator actually requires |

**Backup:** not specified. Postgres data is a named Docker volume (`postgres_data`). That is not a backup strategy.
