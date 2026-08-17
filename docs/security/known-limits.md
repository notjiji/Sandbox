# Known security limits

Documented so operators do not assume controls that are not in the repo.

| Topic | Reality |
|-------|---------|
| Third-party scan authorization | Not implemented |
| API keys | Not implemented (audit names reserved) |
| Billing isolation | Permission only |
| Superuser | `users.is_superuser` exists; not a documented product RBAC path |
| Grafana | Default admin/admin in Compose unless overridden |
| Secrets in `.env.example` | Placeholders; production validator rejects defaults |
| Audit on SQLite tests | No immutability trigger |
| Notification of security events | Stub logger only |
| Agent | Read-only by design; still a credentialed client on `/monitoring` |
| CORS | Reflects configured origins; not a substitute for auth |
| Nmap | If installed in the worker image/host, it will be invoked — image must be treated as trusted |
| Backup | No encrypted backup/restore procedure in-repo |
| Hash chain | Detects mutation of hashed rows; does not by itself stop a DBA from dropping the trigger |
