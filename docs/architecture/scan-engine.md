# Scan engine (as built)

The scan engine is **in-process** (API or Celery worker), not a separate cluster. Full pipeline diagrams: [docs/scan-engine.md](../scan-engine.md). Plugin architecture (Diagram B) and contract: [plugins.md](./plugins.md). Plugin authoring: [docs/plugins/](../plugins/README.md).

## Layers

```
scan_service
  → require_scannable_asset (membership + project + active asset)
  → orchestrator
      → asset adapter (domain asset → ScanTarget)
      → PluginLoader (profile → plugin slugs)
      → each plugin: collect → parse → rules → findings
      → persist scan_plugin_runs + findings
  → risk engine
  → event_bus
```

## Profiles (`app/scans/profiles.py`)

| Profile | Plugins |
|---------|---------|
| `quick` | http_headers, tls, dns, cookies |
| `full` | http_headers, fingerprint, tls, dns, whois, ports, robots, security_txt, cookies, **cve** |
| `custom` | Caller-supplied non-empty slug list |

`ssl` is a registered plugin; it is not on the quick/full default lists (TLS plugin covers that surface on those profiles).

## Plugin loader

`BUILTIN_PLUGIN_CLASSES` also registers **malware, cloud, kubernetes, cve**. Cloud/K8s/malware default `enabled=False`. CVE defaults enabled and is on the full profile. CVE collect uses HTTP headers + service hints and queries OSV — it does not SSH onto the host.

Ports: TCP checks in Python; **Nmap `-sV` only if `nmap` is installed**. Missing Nmap is not a scan error.

## Execution mode

| `ENVIRONMENT` | Default `SCAN_RUN_INLINE` |
|---------------|---------------------------|
| development | true (orchestrator in the API process) |
| staging / production | false (Celery `app.jobs.scans`) |

Override with `SCAN_RUN_INLINE`. Same pattern for `REPORT_RUN_INLINE`.

## Schedules

Table `asset_scan_schedules`. Presets: `quick_daily`, `full_sunday`, `ssl_12h`, `dns_weekly`. Celery beat task `app.jobs.scans.check_due_schedules` every minute.

## Scan authorization (actual)

A scan is allowed when:

1. The caller has `scan:run` (and create as required).
2. The asset exists in the current org/project.
3. `asset_service.require_scannable_asset(...)` resolves that org/project asset.
4. `validate_asset_scannable(asset)` passes.

Today, step 4 means:

- asset status is `active`
- `website`, `domain`, and `public_ip` assets must have ownership verification status `verified`
- for other asset types, ownership verification is enforced when configured

Ownership verification methods supported by the asset API are domain, DNS TXT, HTTP, and IP ownership checks. CIDR/ASN allowlist and "I own this range" workflows are still not implemented.
