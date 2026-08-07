from app.plugins.dns.parser import parse
from app.plugins.dns.schemas import DnsRawResponse, ResolverSnapshot


def test_parse_detects_resolver_discrepancy() -> None:
    raw = DnsRawResponse(
        domain="example.com",
        records={"A": ["203.0.113.10"]},
        resolver_snapshots=[
            ResolverSnapshot(resolver="system", records={"A": ["203.0.113.10"], "MX": []}),
            ResolverSnapshot(resolver="cloudflare", records={"A": ["198.51.100.1"], "MX": []}),
        ],
    )

    parsed = parse(raw)

    assert parsed.resolver_discrepancies
    assert "A differs between system and cloudflare" in parsed.resolver_discrepancies[0]


def test_parse_merges_http_takeover_confirmed() -> None:
    raw = DnsRawResponse(
        domain="example.com",
        records={},
        subdomain_probes=[],
        http_takeover_confirmed=["dev.example.com HTTP fingerprint matches github takeover page"],
    )

    parsed = parse(raw)

    assert parsed.http_takeover_confirmed == raw.http_takeover_confirmed
    assert parsed.subdomain_takeover_risks == raw.http_takeover_confirmed
