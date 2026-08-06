import asyncio
from unittest.mock import MagicMock, patch

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.collector import collect


def test_collect_queries_all_record_types(monkeypatch) -> None:
    def fake_query(resolver, domain, rdtype):
        mapping = {
            "A": (["203.0.113.10"], 3600, None),
            "AAAA": ([], None, "no answer"),
            "MX": (["10 mail.example.com"], 3600, None),
            "TXT": (["v=spf1 -all"], 3600, None),
            "NS": (["ns1.example.com"], 86400, None),
            "SOA": (["ns1.example.com. hostmaster.example.com. 1 7200 3600 1209600 3600"], 3600, None),
            "CNAME": ([], None, "no answer"),
            "DNSKEY": ([], None, "no answer"),
        }
        if domain.startswith("_dmarc."):
            return (["v=DMARC1; p=none"], 3600, None)
        if "._domainkey." in domain:
            return ([], None, "no answer")
        if domain.startswith("_sandbox-probe-"):
            return ([], None, "no answer")
        return mapping.get(rdtype, ([], None, "no answer"))

    monkeypatch.setattr("app.plugins.dns.collector._query", fake_query)
    monkeypatch.setattr("app.plugins.dns.collector._query_dkim", lambda *args, **kwargs: {})

    raw = asyncio.run(
        collect(
            ScanTarget(asset_id="1", identifier="example.com", asset_type="domain"),
            ScanOptions(timeout=5.0),
        )
    )

    assert raw.domain == "example.com"
    assert raw.records["A"] == ["203.0.113.10"]
    assert raw.records["MX"] == ["10 mail.example.com"]
    assert raw.dmarc_records[0].startswith("v=DMARC1")
