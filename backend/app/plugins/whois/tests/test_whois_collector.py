import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.collector import collect


def test_collect_maps_whois_record(monkeypatch) -> None:
    fake_record = {
        "registrar": "Example Registrar, Inc.",
        "creation_date": datetime(2020, 1, 1, tzinfo=UTC),
        "updated_date": datetime(2024, 6, 1, tzinfo=UTC),
        "expiration_date": datetime(2027, 1, 1, tzinfo=UTC),
        "name_servers": ["NS1.EXAMPLE.COM", "ns2.example.com."],
        "org": "Example Org",
        "emails": ["admin@example.com"],
        "text": "Registrar: Example Registrar, Inc.",
    }

    monkeypatch.setitem(__import__("sys").modules, "whois", SimpleNamespace(whois=lambda domain: fake_record))

    raw = asyncio.run(
        collect(
            ScanTarget(asset_id="1", identifier="https://www.example.com", asset_type="domain"),
            ScanOptions(timeout=10.0),
        )
    )

    assert raw.domain == "example.com"
    assert raw.registrar == "Example Registrar, Inc."
    assert raw.name_servers == ["ns1.example.com", "ns2.example.com"]
    assert raw.emails == ["admin@example.com"]
