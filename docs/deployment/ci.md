# CI quality gate

Every **push** and **pull request** runs [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

```
Push / Pull Request
        │
        ▼
Backend tests (pytest)
        │
        ▼
Frontend build (npm run build)
        │
        ▼
Production Docker build (docker-compose.prod.yml)
        │
        ▼
Security / secret checks (gitleaks + repo policy)
        │
        ▼
PASS → merge allowed
FAIL → block
```

## Jobs

| Job | What it proves |
|-----|----------------|
| **Backend tests** | `pytest tests app` on Python 3.12 (SQLite in-memory fixtures) |
| **Frontend build** | `npm ci && npm run build` (TypeScript + Vite production bundle) |
| **Production Docker build** | `docker compose -f docker-compose.prod.yml build` |
| **Security** | Gitleaks scan + `scripts/ci/check-secrets.sh` + test inventory drift check |
| **Quality gate** | Fails if any upstream job failed |

## Local equivalent

```bash
make ci
```

Or step through the same commands manually:

```bash
make test
cd frontend && npm ci && npm run build
docker compose -f docker-compose.prod.yml build
bash scripts/ci/check-secrets.sh
bash scripts/ci/check-test-inventory.sh
```

## Branch protection (recommended)

In GitHub → Settings → Branches → branch protection for `main`:

- Require status check: **Quality gate** (or all CI jobs)
- Require pull request before merge

## What CI does not replace

- Frontend browser e2e
- Live OpenAI / live DNS against the public internet
- Postgres-specific trigger tests (CI uses SQLite for speed)
- Load / performance benchmarks

See [testing/gaps.md](../testing/gaps.md).

## Related

- [testing/inventory.md](../testing/inventory.md) — documented test modules (drift-checked in CI)
- [requirements/traceability-matrix.md](../requirements/traceability-matrix.md) — FR/NFR → tests mapping
- [production.md](./production.md) — production deployment
