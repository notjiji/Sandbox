# Testing gaps (honest)

Relative to a “full platform” checklist. These are **missing or thin**, not implied by green `make test`.

| Expected coverage | Status |
|-------------------|--------|
| Expired / invalid JWT matrix | Not a dedicated suite |
| Ownership transfer integration | Endpoint exists; **no** dedicated integration test called out |
| Member remove / self-remove | Lifecycle exists; coverage thinner than invite/role update |
| Invite resend / list pending | Implemented; not fully tested |
| Org restore | **No product** — nothing to test |
| End-to-end asset → scan → findings → risk → AI → report | **Covered** by `backend/tests/test_product_pipeline.py` (API + real orchestrator; HTTP/DNS/TLS/LLM mocked). Not Playwright. |
| Live OpenAI chat | Tests are mostly offline/prompt; no paid-API integration in CI |
| Frontend unit/e2e | **None** in package scripts |
| Postgres trigger immutability | Not asserted on SQLite |
| Plugin future stubs (cloud/k8s/malware) | Not product-tested as enabled scanners |
| Third-party scan authorization | **Not implemented** — no tests |
| Backup/restore | **Not implemented** |
| Notification delivery | Stub only |
| Load / performance tests | None in-repo |

`make test` passing means the suites above are green, not that every playlist checkbox has an automated test.
