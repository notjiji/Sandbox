# CI quality gate

Every **push** and **pull request** runs [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

```
Push / Pull Request
        │
        ▼
Backend tests (pytest, SQLite; Docker suites excluded)
        │
        ├── Frontend build
        ├── Security / secret checks
        ├── Production Docker build + Caddy validate
        ├── Database restore drill (Compose)
        └── Staging end-to-end (Compose workers + PDF after restart)
        │
        ▼
Quality gate (all jobs must pass)
        │
        ▼
PASS → merge allowed
FAIL → block
```

## Jobs

| Job | What it proves |
|-----|----------------|
| **Backend tests** | `pytest tests app -m "not docker"` on Python 3.12 (SQLite in-memory fixtures) |
| **Frontend build** | `npm ci && npm run build` (TypeScript + Vite production bundle) |
| **Production Docker build** | `docker compose -f docker-compose.prod.yml build` + `scripts/ci/validate-edge.sh` |
| **Security** | Gitleaks scan + `scripts/ci/check-secrets.sh` + test inventory drift check |
| **Database restore drill** | `make backup-integration-test` — encrypted dump → restore into a throwaway DB |
| **Staging end-to-end** | `make staging-acceptance` — Celery path, durable PDF after restart, audit |
| **Quality gate** | Fails if any upstream job failed |

Docker Compose suites are marked `@pytest.mark.docker` so the fast pytest job does not start them twice.

## Local equivalent

Fast checks (same as backend/frontend/build/secrets, no Compose e2e):

```bash
make ci
```

Full quality gate (includes restore drill + staging e2e):

```bash
make ci-full
```

Or step through the same commands manually:

```bash
make test
cd frontend && npm ci && npm run build
docker compose -f docker-compose.prod.yml build
bash scripts/ci/validate-edge.sh
bash scripts/ci/check-secrets.sh
bash scripts/ci/check-test-inventory.sh
make backup-integration-test
make staging-acceptance
```

On-demand staging only: GitHub Actions → **Staging acceptance** (`.github/workflows/staging-acceptance.yml`).

## Branch protection (recommended)

In GitHub → Settings → Branches → branch protection for `main`:

- Require status check: **Quality gate** (or all CI jobs)
- Require pull request before merge

## What CI does not replace

- Frontend browser e2e
- Live OpenAI / live DNS against the public internet
- Postgres-specific trigger tests in the *fast* pytest job (that job uses SQLite)
- Load / performance benchmarks

The restore drill and staging acceptance **do** use real Postgres via Compose.

See [testing/gaps.md](../testing/gaps.md).

## Related

- [testing/inventory.md](../testing/inventory.md) — documented test modules (drift-checked in CI)
- [requirements/traceability-matrix.md](../requirements/traceability-matrix.md) — FR/NFR → tests mapping
- [production.md](./production.md) — production deployment
