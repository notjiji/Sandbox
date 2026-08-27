# Scanner Plugins

Plugins are isolated security checks that run as part of a scan. Each plugin collects raw data, parses it, and emits normalized findings through the declarative rule engine.

**Diagram B and the plugin contract:** [architecture/plugins.md](../architecture/plugins.md) — orchestrator → registry → plugins → normalizer → finding model → risk / AI.

## Overview

```
ScanOrchestrator
    → PluginLoader (select by scan profile)
    → ScanDispatcher (parallel execution)
    → ScannerPlugin / ScannerPipeline
    → ScanNormalizer + RuleEngine
    → findings + scan_plugin_runs
```

**Deep dive:** [../scan-engine.md](../scan-engine.md) — full orchestrator, asset adapter, lifecycle, and persistence.

## Active plugins

| Plugin | Package | Checks |
|--------|---------|--------|
| DNS | `plugins/dns` | DNS records, misconfigurations |
| SSL / TLS | `plugins/ssl`, `plugins/tls` | Certificate validity, protocol issues |
| HTTP headers | `plugins/http_headers` | Security headers (CSP, HSTS, etc.) |
| Cookies | `plugins/cookies` | Cookie flags and policies |
| Ports | `plugins/ports` | Open port detection |
| WHOIS | `plugins/whois` | Domain registration data |
| Robots | `plugins/robots` | robots.txt and sensitive paths |
| Security.txt | `plugins/security_txt` | security.txt presence and content |
| Fingerprint | `plugins/fingerprint` | Technology fingerprinting |

**Future (stubs):** `plugins/future/` — malware, cloud, kubernetes, cve

## Scan profiles

| Profile | Plugins |
|---------|---------|
| `quick` | Subset for fast checks |
| `full` | All active plugins |
| `custom` | User-selected plugin list |

Profiles defined in `backend/app/scans/profiles.py`.

## Key modules

| Module | Path |
|--------|------|
| Plugin base class | `backend/app/plugins/base/plugin.py` |
| Pipeline pattern | `backend/app/plugins/base/pipeline.py` |
| Contracts | `backend/app/plugins/base/contracts.py` |
| Registry / loader | `backend/app/plugins/base/registry.py`, `loader.py` |
| Rule engine | `backend/app/core/rule_engine/` |
| Orchestrator | `backend/app/core/scan_engine/orchestrator.py` |
| External SDK | `scanner-sdk/` |

## Plugin output

Each plugin returns a `ScanResult` with status (`success`, `failed`, `timeout`, `skipped`) and zero or more `ScanFinding` objects. The normalizer converts these into persisted `findings` rows linked to the scan and asset.

## Related docs

- [authoring.md](./authoring.md) — how to build a new plugin
- [../architecture/plugins.md](../architecture/plugins.md) — Diagram B and the plugin contract
- [../findings/README.md](../findings/README.md) — finding model after normalization
- [../jobs/README.md](../jobs/README.md) — async scan execution
