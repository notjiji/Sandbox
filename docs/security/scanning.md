# Scanner security boundaries (as built)

## What we scan

The target is an **asset already in the organization’s project**, with `status=active`. Identity of the target is the asset identifier (URL, host, IP, etc.) stored on the asset.

**Not implemented:** proof that the org owns a public IP, DNS TXT authorization, or an allowlist of CIDRs.

That means a user with `scan:run` can point a scan at any identifier they attach to an asset. Treat that as an **operator-trust** model, not a legal-authorization product.

## Scanner capabilities

Active plugins speak HTTP, TLS, DNS, WHOIS, cookie/header inspection, robots, security.txt, port checks, and OSV CVE lookup from hints. They run from the **backend/worker network**.

Nmap is optional and invoked as `nmap -sV -p <ports> --open -oX - <host>` when present. If Nmap is absent, ports still run without version detection.

Disabled-by-default: cloud, kubernetes, malware plugins.

## Monitoring agent

Enroll only on `server` / `windows_server` / `docker_host`. The agent is designed to be **read-only** on the host (see agent security notes in the agent tree). Heartbeats use agent credentials, not the user’s JWT.

Monitoring alerts ≠ scan findings, except specific derived findings such as `SERVER_OFFLINE`.

## Rate and size

API rate limits apply to HTTP clients, not to how aggressive a plugin is against a target (plugins have their own timeouts). Nginx `client_max_body_size 20m`.
