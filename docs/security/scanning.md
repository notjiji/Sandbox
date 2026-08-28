# Scanner security boundaries (as built)

## Current scan authorization model

The current rule is:

1. User is authenticated.
2. User is acting inside an organization (`X-Organization-ID`).
3. User has the required org-scoped permissions (`scan:create` and `scan:run` as applicable).
4. The target asset exists in that organization's project.
5. The asset passes scannable checks.
6. The scan is created or run.

In code, the create/run path is:

`get_current_membership` -> permission check -> `asset_service.require_scannable_asset(...)` -> `validate_asset_scannable(asset)` -> scan orchestration

Today, `validate_asset_scannable()` checks:

- asset `status` must be `active`
- `website`, `domain`, and `public_ip` assets must have `verification_status=verified`
- for other asset types, if a verification challenge is configured, `verification_status` must be `verified`

The identifier that plugins scan is whatever is stored on the asset metadata / external identifier (URL, domain, host, IP, etc.) after the org member creates or updates that asset.

## Ownership verification (implemented)

The asset API now supports four verification methods:

- Domain verification
- DNS TXT verification
- HTTP verification
- IP ownership verification

Flow:

1. `POST /assets/{asset_id}/verification/challenge` with method.
2. Platform issues a challenge token.
3. Operator publishes token (DNS TXT or well-known HTTP file, depending on method).
4. `POST /assets/{asset_id}/verification/verify` runs validation.
5. Asset verification state becomes `verified` or `failed`.

Verification enforcement is mandatory for `website`, `domain`, and `public_ip` scan targets.

### When verification is cleared

Ownership verification is **reset to `unverified`** when an asset update changes anything that affects **what gets scanned** or **how the target is resolved**. Implementation: `asset_service.update_for_project` in `backend/app/assets/services/asset_service.py`.

| Update field | Clears verification? | Reason |
|--------------|---------------------|--------|
| `name` | **Yes** | Display identity; may affect derived external identifier |
| `type` | **Yes** | Changes scannable surface and plugin targets |
| `metadata` | **Yes** | URL, domain, IP, and other scan identifiers live here |
| `external_identifier` | **Yes** | Direct scan target override |
| `description`, `notes`, `owner`, `business_unit`, `asset_category` | No | Cosmetic / inventory only |
| `environment`, `criticality`, `status` (non-delete), `tags`, `parent_id`, `allow_private_ip` | No | Posture labels and structure, not scan identity |

When cleared, the platform removes `verification_method`, `verification_token`, timestamps, and last error. The asset must complete challenge → verify again before the next scan on `website`, `domain`, or `public_ip`.

Tests: `tests/test_asset_verification.py` (`test_identity_field_update_clears_verification`, `test_cosmetic_update_preserves_verification`).

## Scanner capabilities

Active plugins speak HTTP, TLS, DNS, WHOIS, cookie/header inspection, robots, security.txt, port checks, and OSV CVE lookup from hints. They run from the **backend/worker network**.

Nmap is optional and invoked as `nmap -sV -p <ports> --open -oX - <host>` when present. If Nmap is absent, ports still run without version detection.

Disabled-by-default: cloud, kubernetes, malware plugins.

## Monitoring agent

Enroll only on `server` / `windows_server` / `docker_host`. The agent is designed to be **read-only** on the host (see agent security notes in the agent tree). Heartbeats use agent credentials, not the user’s JWT.

Monitoring alerts ≠ scan findings, except specific derived findings such as `SERVER_OFFLINE`.

## Rate and size

API rate limits apply to HTTP clients, not to how aggressive a plugin is against a target (plugins have their own timeouts). Nginx `client_max_body_size 20m`.
