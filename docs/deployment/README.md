# Deployment

Docker Compose is the documented runtime for local and small-team deployments. There is no in-repo Kubernetes/Helm chart.

| Document | Covers |
|----------|--------|
| [Installation](./installation.md) | `git clone` → `.env` → `docker compose up` — **what happens at each step** |
| [Configuration](./configuration.md) | All environment variables and Compose overrides |
| [Production](./production.md) | Production validator, hardening checklist, scaling notes |
| [Production runbook](./production-runbook.md) | Startup, health, logs, restart, migrate, backup, incidents |
| [Backups](./backups.md) | Postgres policy (daily / 7-day / encrypted / monthly restore test); reports, config, Redis |
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

**Backup:** automated in production Compose — [backups.md](./backups.md).
