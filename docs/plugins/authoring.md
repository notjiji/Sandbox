# Plugin Authoring Guide

This guide supplements [../scan-engine.md](../scan-engine.md) with a practical checklist for adding a scanner plugin.

**Contract (inputs, outputs, isolation):** [../architecture/plugins.md](../architecture/plugins.md). Do not write findings or scores from inside a plugin.

## Recommended pattern: `ScannerPipeline`

Most plugins use the three-stage pipeline:

```
Collector  →  raw response (HTTP, DNS, socket, …)
Parser     →  structured parsed data
RuleEngine →  declarative findings from catalog rules
```

Example structure (see `plugins/http_headers/`):

```
plugins/my_plugin/
├── plugin.py      # ScannerPipeline subclass, wires collector/parser
├── collector.py   # async data fetch
├── parser.py      # normalize raw → parsed schema
├── schemas.py     # Pydantic types
└── tests/
```

## Minimal plugin skeleton

```python
# plugins/my_plugin/plugin.py
from app.plugins.base.pipeline import ScannerPipeline
from app.plugins.base.contracts import ScanOptions, ScanResult

class MyPlugin(ScannerPipeline[MyRaw, MyParsed]):
    name = "my_plugin"
    version = "1.0.0"
    supported_asset_types = frozenset({"website"})

    async def run(self, asset, options: ScanOptions) -> ScanResult:
        return await super().run(asset, options)
```

## Register the plugin

1. Add the plugin package under `backend/app/plugins/`
2. Register in `backend/app/plugins/registry.py` (or ensure auto-discovery picks it up)
3. Add catalog rules in `backend/app/core/rule_engine/catalog_*.py` if using declarative rules
4. Include in scan profile(s) in `backend/app/scans/profiles.py`
5. Add tests under `plugins/my_plugin/tests/`

## Rules of thumb

- **No ORM in plugins** — receive a `ScanTarget`, not a SQLAlchemy model
- **Timeout-friendly** — respect `ScanOptions` timeouts; return `ScanResult.timeout()` on expiry
- **Idempotent findings** — use stable `finding_code` values so re-scans update rather than duplicate
- **Evidence in findings** — store reproducible proof (header values, cert expiry date, port list)

## Testing

Run plugin unit tests:

```bash
cd backend
python -m pytest app/plugins/my_plugin/tests/ -q
```

Run scan engine integration tests:

```bash
python -m pytest app/core/scan_engine/tests.py -q
```

## Scanner SDK

For external or standalone scanners, see `scanner-sdk/` for shared contracts compatible with the platform normalizer.
