# Test strategy (as built)

## Command

```bash
make test
# → cd backend && pip install -q -r requirements-dev.txt && python -m pytest tests app -q -m "not docker"
```

`pytest.ini`: `testpaths = tests app`, files `test_*.py`, `*_test.py`, `tests.py`, `lifecycle_tests.py`. Markers: `integration`, `docker` (Compose suites; required CI jobs via `make staging-acceptance` and `make backup-integration-test`).

## Layers

| Layer | Location | Typical style |
|-------|----------|----------------|
| Feature unit/module | `backend/app/<feature>/tests.py` | Model/tablename and small unit checks |
| API / integration | `backend/tests/test_*.py` | HTTP + DB via shared fixtures in `tests/support.py`. `test_product_pipeline.py` is the full product path. |
| Plugin | `backend/app/plugins/*/tests` (where present) | Plugin parse/rules |
| Scan engine | `backend/app/core/scan_engine/tests.py` | Orchestrator pieces |

## Database under test

Tests use an isolated DB (SQLite `create_all` in the usual harness), **not** the Docker Postgres Alembic history. Implications:

- Postgres-only objects (audit immutability trigger, some enums) are not fully exercised unless a test hits real Postgres.
- Do not assume `audit_logs` is empty at test start if the suite shares a DB; filter by action/id.

## Auth in tests

Support helpers issue tokens and memberships. There is **no** dedicated “expired JWT” suite called out by name (see [gaps](./gaps.md)).

## Frontend

No Jest/Vitest script in `frontend/package.json`. UI regressions are not automated in-repo today.
