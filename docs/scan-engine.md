# Scan Engine Architecture

This document describes how assets flow into the scan engine, how the **Scan Orchestrator** coordinates plugins, and how results are persisted. It covers the **Asset Adapter**, plugin execution, per-plugin status tracking, and the asset list tree view.

---

## Overview

Scans are project-scoped and run against **active** assets. The system deliberately separates concerns:

| Layer | Responsibility | Touches ORM? |
|-------|----------------|--------------|
| **Asset Adapter** | Load DB assets, produce normalized scan targets | Yes (only here for scanning) |
| **Scan Orchestrator** | Load plugins, run pipeline, combine results | No |
| **Scanner Plugins** | Execute checks against a `ScanTarget` | No |
| **Scan Service (API)** | HTTP endpoints, audit, transaction commit | Via services only |

**End-to-end path:**

```
POST /projects/{id}/assets/{id}/scans/{id}/run
  → scan_service.run_asset_scan()
  → ScanOrchestrator.execute()
  → AssetAdapter → plugins → normalizer → findings + plugin_runs
```

Apply migration `014` before running scans with plugin status tracking:

```bash
alembic upgrade head
```

---

## 1. High-Level Flow

```mermaid
flowchart TB
    subgraph API["API Layer"]
        RUN["POST /assets/{id}/scans/{id}/run"]
        GET["GET /assets/{id}/scans/{id}"]
    end

    subgraph AssetDomain["Asset Domain (ORM-aware)"]
        DB[("Database Asset\n+ metadata + children")]
        ADAPT["AssetAdapter.adapt()"]
        NORM["NormalizedScanTarget"]
        FLAT["AssetAdapter.to_plugin_targets()"]
    end

    subgraph ScanEngine["Scan Engine (ORM-free)"]
        ORCH["ScanOrchestrator"]
        LOAD["PluginLoader.select_for_scan()"]
        DISP["ScanDispatcher"]
        NORMF["ScanNormalizer"]
        COMB["Result Combiner"]
    end

    subgraph Plugins["Scanner Plugins"]
        P1["dns"]
        P2["ssl"]
        P3["http_headers"]
        P4["..."]
    end

    subgraph Persistence["Persistence"]
        SPR[("scan_plugin_runs")]
        FIND[("findings")]
        SCAN[("scans")]
    end

    RUN --> ORCH
    ORCH --> ADAPT
    DB --> ADAPT --> NORM --> FLAT
    ORCH --> LOAD
    LOAD --> DISP
    FLAT --> DISP
    DISP --> P1 & P2 & P3 & P4
    P1 & P2 & P3 & P4 --> DISP
    DISP --> NORMF --> COMB
    ORCH --> SPR
    COMB --> FIND
    ORCH --> SCAN
    GET --> SCAN & SPR
```

---

## 2. Scan Orchestrator — Step by Step

The orchestrator owns the full plugin pipeline:

1. **Load enabled plugins** for the scan type
2. **Adapt asset** into normalized scan targets (root + children)
3. **Run each plugin** per target, catching failures in isolation
4. **Save plugin status** to `scan_plugin_runs`
5. **Normalize** raw plugin output via `ScanNormalizer`
6. **Combine** normalized findings across all plugins and targets
7. **Persist findings** and resolve final scan status

```mermaid
flowchart TD
    START([execute scan]) --> A

    A["1. Load enabled plugins\nPluginLoader.select_for_scan() → Registry"]
    A --> B{Any plugins\nconfigured?}
    B -->|No| FAIL1["Scan → FAILED"]
    B -->|Yes| C

    C["2. Adapt asset\nAssetAdapter → NormalizedScanTarget → ScanTarget[]"]
    C --> D{Adapt OK?}
    D -->|No| FAIL2["Scan → FAILED"]
    D -->|Yes| E

    E["3. For each target × enabled plugin"]
    E --> F

    subgraph PerPlugin["Per plugin run (isolated)"]
        F["Create scan_plugin_run\nstatus = RUNNING"]
        F --> G["4. Run plugin\nScanDispatcher.dispatch()"]
        G --> H{Success?}
        H -->|Exception / failure| I["Save status = FAILED\n+ error_message"]
        H -->|Success| J["5. Call normalizer\nScanNormalizer.normalize_findings()"]
        J --> K["Save status = COMPLETED\n+ findings_count"]
        I --> L["PluginExecutionRecord"]
        K --> L
    end

    L --> M{More plugins\nor targets?}
    M -->|Yes| E
    M -->|No| N

    N["6. Combine results\nmerge all normalized findings"]
    N --> O["7. Persist findings\ncreate_finding() per record"]
    O --> P{Any plugin\ncompleted?}
    P -->|Yes| OK["Scan → COMPLETED"]
    P -->|No| FAIL3["Scan → FAILED"]

    FAIL1 --> END([return scan])
    FAIL2 --> END
    FAIL3 --> END
    OK --> END
```

**Important:** One plugin failing does **not** stop the others. The scan is marked **COMPLETED** if **any** plugin succeeds (partial success). It is **FAILED** only when every plugin fails or skips, or when asset adaptation fails.

---

## 3. Asset Adapter Boundary

The adapter is the **only** component that loads ORM `Asset` models for scanning. Everything downstream receives plain data objects.

```mermaid
flowchart LR
    subgraph ORM["Only AssetAdapter touches ORM"]
        ASSET[("Asset row")]
        META[("AssetMetadataEntry")]
        CHILD[("Child assets")]
    end

    subgraph Normalized["Scan engine sees this"]
        NST["NormalizedScanTarget\n• asset_id, identifier\n• asset_type, environment\n• metadata dict\n• related_targets[]"]
        ST["ScanTarget (plugin contract)\n• asset_id\n• identifier\n• asset_type"]
    end

    subgraph Consumers["Consumers"]
        ORCH["ScanOrchestrator"]
        PLUG["ScannerPlugin.scan()"]
    end

    ASSET --> ADAPT["AssetAdapter"]
    META --> ADAPT
    CHILD --> ADAPT
    ADAPT --> NST
    NST --> TO["to_plugin_targets()"]
    TO --> ST
    ST --> ORCH --> PLUG
```

### Type reference

| Type | Location | Purpose |
|------|----------|---------|
| `NormalizedScanTarget` | `app.assets.schemas` | Rich, asset-type-agnostic view for the scan engine |
| `ScanTarget` | `app.plugins.base` | Minimal dataclass passed to every plugin |
| `ScanTargetContext` | `app.assets.schemas` | Alias for `NormalizedScanTarget` (backward compatible) |

### Hierarchy expansion

Parent assets expand into multiple plugin targets:

| Parent type | Child types included in scan |
|-------------|------------------------------|
| `website` | `public_ip` |
| `domain` | `email_domain` |
| `cloud_account` | `s3_bucket` |

---

## 4. Base Plugin Interface

Every scanner plugin inherits the same interface. Plugins receive a normalized `ScanTarget` (the plugin-facing asset contract):

```python
class ScannerPlugin(ABC):
    name: str                  # slug, e.g. "ssl"
    description: str           # human label, e.g. "SSL Scanner"
    version: str
    supported_assets: list[str]
    supported_scan_types: list[str]
    enabled: bool = True

    async def scan(self, asset: ScanTarget) -> ScanResult:
        ...
```

Example implementation (real scanners delegate to the shared pipeline):

```python
class SslPlugin(ScannerPlugin):
    name = "ssl"
    description = "SSL Scanner"
    version = "3.1.0"
    supported_assets = ["website", "domain", "api_endpoint", "email_domain"]
    supported_scan_types = [ScanType.FULL.value, ScanType.QUICK.value]

    async def scan(self, asset: ScanTarget) -> ScanResult:
        raw = await collect_ssl_data(asset)
        parsed = parse_ssl_data(raw)
        return evaluate_rules(parsed, asset)
```

Built-in plugins are registered in one place — no string import paths scattered across the codebase:

```python
# app/plugins/base/loader.py
BUILTIN_PLUGIN_CLASSES = [
    HttpHeadersPlugin,
    SslPlugin,
    TlsPlugin,
    DnsPlugin,
    WhoisPlugin,
    PortsPlugin,
    RobotsPlugin,
    CookiesPlugin,
    MalwarePlugin,      # disabled by default
    CloudPlugin,        # disabled by default
    KubernetesPlugin,   # disabled by default
    CvePlugin,
]
```

---

## 5. Scan Profiles

Instead of always running every scanner, scans use **reusable profiles** that define which plugins to execute. This improves usability and performance.

| Profile | Plugins |
|---------|---------|
| **Quick Scan** | `http_headers`, `ssl`, `dns`, `cookies` |
| **Full Scan** | `http_headers`, `ssl`, `tls`, `dns`, `whois`, `ports`, `robots`, `cookies`, `cve` |
| **Custom Scan** | User-selected plugins (stored on the scan as `selected_plugins`) |

```mermaid
flowchart TB
    CREATE["POST /assets/{id}/scans\n{ scan_type, plugins? }"]
    CREATE --> PROFILE["resolve_profile_plugins()"]
    PROFILE --> QUICK["quick → http_headers, ssl, dns, cookies"]
    PROFILE --> FULL["full → 9 plugins incl. whois, ports, cve"]
    PROFILE --> CUSTOM["custom → user plugins[]"]

    RUN["POST /scans/{id}/run"] --> LOADER["PluginLoader.select_for_scan(scan)"]
    LOADER --> REG["registry.resolve_plugin_names()"]
    REG --> EXEC["Run enabled plugins for asset targets"]
```

- `GET /projects/{id}/assets/{id}/scans/profiles` — list profiles with labels, descriptions, and plugin slugs
- Custom scans require `plugins: string[]` in the create request
- Profile plugin lists live in `backend/app/scans/profiles.py`

Apply migration `016` for the `custom` scan type and `selected_plugins` column:

```bash
alembic upgrade head
```

---

## 6. Plugin Registry

Instead of hardcoding plugin lists in the orchestrator, the **registry** is the single source of truth:

```mermaid
flowchart TB
    BUILTIN["BUILTIN_PLUGIN_CLASSES\n[HttpHeadersPlugin, SslPlugin, DnsPlugin, ...]"]
    BUILTIN --> DISCOVER["discover_plugins(registry)"]
    DISCOVER --> REG["PluginRegistry"]

    ORCH["ScanOrchestrator"] --> LOADER["PluginLoader.select_for_scan(scan)"]
    LOADER --> ASK["resolve_profile_plugins() → registry.resolve_plugin_names()"]
    ASK --> REG

    REG --> CHECK{enabled?}
    CHECK -->|Yes| FILTER["Filter by supported_assets per target"]
    CHECK -->|No| SKIP["Excluded from profile or disabled"]

    FILTER --> RUN["Run plugin.scan(asset)"]
    RUN --> SPR[("scan_plugin_runs")]
```

The orchestrator resolves plugins from the scan profile:

```
Profile → plugin slugs → Registry → enabled ScannerPlugin instances
         → filter by supported_assets per target
```

### Built-in plugins

| Plugin | Version | Description | Scan types | Supported assets |
|--------|---------|-------------|------------|------------------|
| `http_headers` | 3.1 | HTTP security headers, cookies, mixed content | full, quick | website, api_endpoint |
| `ssl` | 3.1 | TLS/certificate analysis, CT issuers, OCSP | full, quick | website, domain, api_endpoint, email_domain |
| `tls` | 1.0 | Extended TLS checks (stub) | full | website, domain, api_endpoint |
| `dns` | 3.1 | DNS records, SPF/DMARC/DKIM, DNSSEC, takeover | full, quick | website, domain, public_ip, email_domain |
| `whois` | 2.0 | Registrar, expiry, privacy, nameservers | full | domain, email_domain |
| `ports` | 3.0 | TCP connect + banner + optional Nmap `-sV` | full | public_ip, server, windows_server, docker_host |
| `robots` | 1.0 | robots.txt analysis | full | website, api_endpoint |
| `cookies` | 1.0 | Cookie security attributes | full, quick | website, api_endpoint |
| `cve` | 1.0 | OSV vulnerability lookup from banners/headers | full, custom | server, public_ip, website, … |

Every real scanner follows the same internal pipeline:

```
collect → parse → evaluate_rules → ScanResult
```

Plugins can be disabled via `PluginConfig.enabled = False`. Disabled plugins are excluded from profile resolution.

### Port scanner pipeline

The port scanner (`ports` v3) uses the richest detection path available:

```mermaid
flowchart TD
    A[TCP connect scan] --> B{Port open?}
    B -->|No| SKIP[Skip port]
    B -->|Yes| C[Grab protocol banner]
    C --> D[Extract version from banner]
    D --> E{Nmap installed?}
    E -->|Yes| F["nmap -sV on open ports"]
    E -->|No| G[Use banner-only data]
    F --> H[Merge product/version]
    G --> H
    H --> I[Parser: port → service → product → version]
    I --> J[Rule engine → findings]
```

**Example parsed service:** port `22` → service `ssh` → product `OpenSSH` → version `9.2`

**Rules:** `PORT_FTP_OPEN`, `PORT_TELNET_OPEN`, `PORT_RDP_EXPOSED`, `PORT_MYSQL_PUBLIC`, `PORT_REDIS_PUBLIC`, `PORT_MONGODB_PUBLIC`

Install **Nmap** and **OpenSSL** in the scan worker for richest results. The backend Docker image includes both:

```dockerfile
RUN apt-get install -y nmap openssl
```

Rebuild workers after changing the Dockerfile:

```bash
docker compose build backend celery-worker
docker compose up -d backend celery-worker
```

### Plugin run statuses

| Status | Meaning |
|--------|---------|
| `pending` | Created, not yet started |
| `running` | Plugin execution in progress |
| `completed` | Plugin finished successfully |
| `failed` | Plugin error or returned failure |
| `skipped` | Disabled |

### Adding a new plugin

1. Create `app/plugins/my_scanner/plugin.py` implementing `ScannerPlugin`
2. Add the class to `BUILTIN_PLUGIN_CLASSES` in `app/plugins/builtin.py`
3. No orchestrator changes required — the registry picks it up automatically

---

## 7. Scan Lifecycle

Every scan moves through explicit states. Each transition is validated and timestamped on the `scans` row.

```mermaid
stateDiagram-v2
    [*] --> Pending: create scan
    Pending --> Queued: POST /run
    Pending --> Cancelled: cancel
    Queued --> Running: worker picks up
    Queued --> Cancelled: cancel
    Running --> Completed: plugins succeed
    Running --> Failed: all plugins fail / fatal error
    Running --> Cancelled: cancel
    Failed --> Queued: retry
    Completed --> [*]
    Cancelled --> [*]
    Failed --> [*]
```

| Status | Meaning | Timestamp column |
|--------|---------|------------------|
| `pending` | Created, waiting to be started | `pending_at` |
| `queued` | Accepted for execution | `queued_at` |
| `running` | Plugins executing | `running_at` |
| `completed` | At least one plugin succeeded | `completed_at` |
| `failed` | No plugins succeeded / fatal error | `failed_at` |
| `cancelled` | Stopped before completion | `cancelled_at` |

- `POST /run` transitions **pending → queued**, then enqueues `app.jobs.scans.execute_scan` (Celery).
- In development, `SCAN_RUN_INLINE=true` (default) runs the queued scan immediately in-process after queuing.
- The API returns a `lifecycle` object on every scan with all transition timestamps.

Apply migration `017` for the `queued` status and lifecycle timestamp columns.

---

## 8. Data Written Per Scan Run

```mermaid
erDiagram
    SCAN ||--o{ SCAN_PLUGIN_RUN : has
    SCAN ||--o{ FINDING : produces
    ASSET ||--o{ SCAN_PLUGIN_RUN : "target of"
    ASSET ||--o{ FINDING : "attributed to"

    SCAN {
        uuid id
        enum status
        enum scan_type
        jsonb selected_plugins
        timestamp pending_at
        timestamp queued_at
        timestamp running_at
        timestamp completed_at
        timestamp failed_at
        timestamp cancelled_at
    }

    SCAN_PLUGIN_RUN {
        uuid id
        uuid scan_id
        uuid asset_id
        string plugin_name
        enum status
        string error_message
        int findings_count
    }

    FINDING {
        uuid id
        uuid scan_id
        uuid asset_id
        string title
        enum severity
    }
```

**Example:** A **FULL** scan on a **website** with one **public_ip** child runs each enabled plugin against **both** targets. Findings are attributed to the correct `asset_id`. Plugin runs are unique per `(scan_id, asset_id, plugin_name)`.

### API response

`GET /projects/{project_id}/assets/{asset_id}/scans/{scan_id}` and the response from `POST .../run` include `plugin_runs[]` with per-plugin status.

---

## 7. Asset List Tree View

The frontend asset list supports an expandable tree so pagination applies to **root assets only**, avoiding split parent/child pages.

```mermaid
flowchart TB
    LIST["GET /assets?roots_only=true\n(paginate roots only)"]
    LIST --> ROOTS["Page of root assets\nwebsites, domains, servers..."]
    ROOTS --> EXPAND{User expands row}
    EXPAND --> CHILDREN["GET /assets/{id}/children"]
    CHILDREN --> INLINE["Render children inline\npublic_ip, email_domain, s3_bucket"]
```

### View modes

| Mode | API | Behavior |
|------|-----|----------|
| **Tree** (default) | `?roots_only=true` | Paginate roots; expand to load children |
| **Flat** | Standard list | All matching assets on one paginated list |

Tree view auto-disables when **searching** or filtering by **child asset types** (`public_ip`, `email_domain`, `s3_bucket`).

### Related API

| Endpoint / param | Purpose |
|------------------|---------|
| `GET /assets?roots_only=true` | Root assets only |
| `GET /assets/{id}/children` | Direct children for expand |
| `GET /assets?parent_id={uuid}` | Alternative children listing |

---

## Key Files

### Asset domain

| File | Role |
|------|------|
| `backend/app/assets/adapter.py` | `AssetAdapter` — DB → normalized targets |
| `backend/app/assets/schemas.py` | `NormalizedScanTarget`, `AssetSummary` |
| `backend/app/assets/metadata.py` | Primary identifier resolution |
| `backend/app/assets/repositories/asset_repository.py` | List, roots_only, children queries |

### Scan engine

| File | Role |
|------|------|
| `backend/app/core/scan_engine/orchestrator.py` | `ScanOrchestrator` — pipeline entry point |
| `backend/app/core/scan_engine/normalizer.py` | Raw findings → normalized dicts |
| `backend/app/core/scan_engine/result_combiner.py` | Combine findings, resolve scan status |
| `backend/app/plugins/output.py` | `PluginOutput`, `PluginFinding`, `make_finding()` |
| `backend/app/plugins/config.py` | `PluginConfig` — enabled, timeout, retries, parallel, version |
| `backend/app/plugins/builtin.py` | `BUILTIN_PLUGIN_CLASSES` — single registration list |
| `backend/app/plugins/registry.py` | `PluginRegistry.get_enabled_plugins()` |
| `backend/app/core/scan_engine/plugin_loader.py` | `PluginLoader.select_for_scan()` |
| `backend/app/core/scan_engine/dispatcher.py` | Invoke async plugins, catch exceptions |

### Scans and plugins

| File | Role |
|------|------|
| `backend/app/scans/lifecycle.py` | Valid transitions + timestamp stamping |
| `backend/app/scans/services/scan_executor.py` | Queued → running → completed/failed |
| `backend/app/jobs/scans.py` | Celery task for async scan execution |
| `backend/app/scans/profiles.py` | Quick / Full / Custom profile → plugin mappings |
| `backend/app/scans/services/scan_service.py` | Create, run, get scans |
| `backend/app/scans/models.py` | `Scan`, `ScanPluginRun` |
| `backend/app/scans/repositories/scan_plugin_repository.py` | Plugin run persistence |

### Frontend

| File | Role |
|------|------|
| `frontend/src/features/assets/pages/Assets.jsx` | Tree/flat toggle, expand state |
| `frontend/src/features/assets/components/AssetTable.jsx` | Hierarchical row rendering |
| `frontend/src/features/assets/utils/hierarchy.js` | Tree row builders |

### Migrations

| Revision | Description |
|----------|-------------|
| `014_scan_plugin_runs.py` | `scan_plugin_runs` table + `plugin_run_status` enum |
| `016_scan_profiles.py` | `custom` scan type + `selected_plugins` column |
| `017_scan_lifecycle.py` | `queued` status + lifecycle timestamp columns |
| `030_scanner_risk_rules.py` | DNS/HTTP/SSL finding codes for risk engine |
| `031_section7_gap_risk_rules.py` | DNSSEC, CT, CSP, port, CVE rules |
| `032_whois_risk_rules.py` | WHOIS expired/privacy/registrar rules |
| `033_port_scanner_risk_rules.py` | Port exposure rules (FTP, RDP, MySQL, Redis, MongoDB) |

Apply all migrations before running scans:

```bash
cd backend
alembic upgrade head
```

---

## 8. Plugin Output

Every plugin returns the **exact same structure** — no exceptions. This makes aggregation simple.

```json
{
  "plugin": "ssl",
  "status": "completed",
  "duration": 1.42,
  "findings": [],
  "metadata": {}
}
```

Defined in `app/plugins/output.py` as `PluginOutput`. Failed runs use `"status": "failed"` with an `error` field.

```mermaid
flowchart LR
    PLUGIN["ScannerPlugin.scan()"] --> OUT["PluginOutput"]
    OUT --> ORCH["ScanOrchestrator"]
    ORCH --> NORM["ScanNormalizer.normalize_output()"]
    NORM --> DB[("findings + scan_plugin_runs")]
```

---

## 9. Finding Model

Every finding follows one schema. Plugins convert raw results into `PluginFinding` **before returning**:

| Field | Description |
|-------|-------------|
| `plugin` | Source scanner slug |
| `title` | Short summary |
| `description` | Detailed explanation |
| `severity` | critical / high / medium / low / info |
| `evidence` | Proof or observation |
| `recommendation` | Remediation guidance |
| `references` | External links (CVE, OWASP, etc.) |
| `raw_data` | Original structured payload |
| `confidence` | 0.0–1.0 score |
| `detected_at` | When the issue was observed |

Use the `make_finding()` helper in `app/plugins/output.py` to build findings consistently.

Persisted to the `findings` table (migration `015`).

---

## 10. Plugin Metadata

Each plugin can return arbitrary **metadata** alongside findings. Metadata is displayed on the asset page but does not necessarily affect risk scoring.

| Plugin | Example metadata |
|--------|------------------|
| **SSL** | host, port, protocols, issuer, expires, cipher, sans |
| **WHOIS** | registrar, created, updated, expires, name_servers, privacy_enabled |
| **HTTP** | url, status_code, server, redirect_count, security_headers |
| **DNS** | records, spf, dmarc, dkim_selectors, dnssec, takeover risks |
| **Ports** | open_ports, services (port/service/product/version) |
| **CVE** | cve_count, vulnerable packages |

Stored on `scan_plugin_runs.metadata` and returned in `ScanPluginRunSummary.metadata`.

---

## 11. Plugin Configuration

Each plugin exposes its own configuration via `PluginConfig`:

| Setting | Purpose |
|---------|---------|
| `enabled` | Toggle plugin on/off |
| `timeout` | Max seconds before timeout |
| `retries` | Retry count on transient failure |
| `parallel` | Allow parallel execution hint |
| `version` | Plugin version string |

```python
default_config = PluginConfig(
    enabled=True,
    timeout=45.0,
    retries=2,
    parallel=False,
    version="3.1.0",
)
```

Administrators can tune scanner behavior without code changes. Inspect all plugin configs via `registry.get_plugin_configs()`.

---

## Design Principles

1. **Plugins never touch the database** — they receive only `ScanTarget`.
2. **Asset Adapter is the scan boundary** — ORM loading and hierarchy resolution live in one place.
3. **Plugin failures are isolated** — one bad plugin does not abort the entire scan.
4. **Status is observable** — every plugin run is recorded for debugging and UI.
5. **New plugins** — add a class + register in `BUILTIN_PLUGIN_CLASSES`; no orchestrator changes.
6. **New asset types** — add metadata/adapter logic; plugins declare `supported_assets`.
8. **Standard output** — every plugin returns `PluginOutput`; aggregation is uniform.
9. **Rich findings** — plugins produce full `PluginFinding` objects before returning.

---

## Related Documentation

- Asset hierarchy rules: `backend/app/assets/enums.py` (`CHILD_PARENT_MAP`)
- Scan permissions: `backend/app/scans/permissions.py` and `app/core/permissions.py`
- Unit tests: `backend/app/core/scan_engine/tests.py`
