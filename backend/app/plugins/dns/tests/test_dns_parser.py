from app.plugins.dns.parser import parse
from app.plugins.dns.schemas import DnsRawResponse


def test_parse_detects_spf_absence() -> None:
    raw = DnsRawResponse(domain="example.com", records={"A": ["203.0.113.10"]})
    parsed = parse(raw)
    assert parsed.has_spf is False
    assert parsed.a_records == ["203.0.113.10"]
