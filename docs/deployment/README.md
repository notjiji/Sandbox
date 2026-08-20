# Deployment

Docker Compose is the documented runtime for local and small-team deployments. There is no in-repo Kubernetes/Helm chart.

| Document | Covers |
|----------|--------|
| [Installation](./installation.md) | `git clone` → `.env` → `docker compose up` — **what happens at each step** |
| [Configuration](./configuration.md) | All environment variables and Compose overrides |
| [Production](./production.md) | Production validator, hardening checklist, scaling notes |
| [Backups](./backups.md) | Manual Postgres/report backup and restore (no automated job) |
| [Troubleshooting](./troubleshooting.md) | Common failures and fixes |

## Supplementary reference

| Document | Covers |
|----------|--------|
| [Docker Compose services](./docker.md) | Service list and volume mounts |
| [Environment (quick ref)](./environment.md) | Legacy variable table |
| [Health probes](./health.md) | `/health`, `/health/live`, `/health/ready` |
| [Local setup](./local.md) | Makefile targets and URLs |

## Quick start

```bash
git clone <repository-url> sandbox && cd sandbox
cp .env.example .env
docker compose up -d    # or: make up
make migrate            # required — schema not applied automatically
make seed               # optional demo tenant
```

Open http://localhost — see [installation.md](./installation.md) for the full boot sequence.

**Backup:** not automated. Postgres uses volume `postgres_data`. See [backups.md](./backups.md).
