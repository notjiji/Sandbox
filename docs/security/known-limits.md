# Known security limits

Documented so operators do not assume controls that are not in the repo.

| Topic | Reality |
|-------|---------|
| Third-party scan authorization | Implemented for asset-level challenge/verify flows (domain, DNS TXT, HTTP, IP). Mandatory for `website`, `domain`, and `public_ip` scan targets. |
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
| Backup | No automated backup job in-repo. Operator policy (daily / 7-day / encrypted offsite / monthly restore test) is documented in [deployment/backups.md](../deployment/backups.md). Redis is ephemeral, not business data. |
| Hash chain | Detects mutation of hashed rows; does not by itself stop a DBA from dropping the trigger |
