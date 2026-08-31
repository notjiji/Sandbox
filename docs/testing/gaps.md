# Testing gaps (honest)

Relative to a “full platform” checklist. These are **missing or thin**, not implied by green `make test`.

| Expected coverage | Status |
|-------------------|--------|
| Expired / invalid JWT matrix | **Covered** by `backend/tests/test_jwt_security.py` (expired, invalid signature, malformed, refresh rotation/logout, session mismatch). |
| Ownership transfer integration | Endpoint exists; **no** dedicated integration test called out |
| Member remove / self-remove | Lifecycle exists; coverage thinner than invite/role update |
| Invite resend / list pending | Implemented; not fully tested |
| Org restore | **No product** — nothing to test |
| End-to-end asset → verify → scan → findings → risk → AI → report | **Covered** by `backend/tests/test_product_pipeline.py` (inline/dev). Staging worker path + PDF after restart: `tests/test_staging_acceptance.py` (Docker, manual/`make staging-acceptance`). Not Playwright. |
| Ownership verification invalidation rules | **Covered** by `tests/test_asset_verification.py` (identity vs cosmetic updates) |
| Live OpenAI chat | Tests are mostly offline/prompt; no paid-API integration in CI |
| Frontend unit/e2e | **None** in package scripts |
| Postgres trigger immutability | Not asserted on SQLite |
| Plugin future stubs (cloud/k8s/malware) | Not product-tested as enabled scanners |
| CIDR/ASN scan authorization | **Not implemented** — no tests (asset-level challenge/verify **is** implemented) |
| Backup/restore automation | **Implemented** — `infrastructure/backup/`, `tests/test_backup_restore.py` |
| CI quality gate | **Implemented** — [deployment/ci.md](../deployment/ci.md) |
| Staging acceptance (workers + durable PDF + restart) | **Implemented** — `make staging-acceptance`, [deployment/staging.md](../deployment/staging.md) |
| Notification delivery | Stub only |
| Load / performance tests | None in-repo |

`make test` passing means the suites above are green, not that every playlist checkbox has an automated test.
