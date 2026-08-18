# Platform goal

Sandbox is a **multi-tenant security assessment platform** (see the [product definition](./definition.md)). An organization inventories digital assets, runs plugin-based scans, reviews findings, sees a deterministic risk score, and uses dashboard, PDF reports, and an org-scoped AI assistant to act on the results. Server-like assets can also enroll a read-only monitoring agent.

The product is an **internal assessment tool for assets the organization already manages**. It is not a general-purpose attack platform, and it does not implement third-party scan authorization or IP-ownership proof.

## What the product optimizes for

1. **Tenant isolation** — work stays inside one organization, selected with `X-Organization-ID`.
2. **Repeatable assessment** — scans use named plugin profiles; risk is rule-based, not model-invented.
3. **Operator workflow** — register assets, scan, triage findings, report, optionally chat with AI over structured facts.
4. **Accountability** — meaningful actions are written to append-only audit logs (see [audit](../security/audit.md)).

## What it is not (today)

- Not a SIEM product. Audit rows can be forwarded to an external SIEM; default sink is `none`.
- Not a notification or webhook platform. Those subscribers exist as stubs.
- Not a full cloud/K8s/malware scanner. Those plugins are registered but disabled or preview-only except CVE lookup on the full profile.
- Not a billed SaaS with API keys. Billing permission exists on the owner role; there is no billing product or API-key surface.
