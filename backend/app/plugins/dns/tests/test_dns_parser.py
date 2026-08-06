from app.plugins.dns.parser import parse
from app.plugins.dns.schemas import DnsRawResponse


def test_parse_detects_spf_dmarc_dkim_and_dnssec() -> None:
    raw = DnsRawResponse(
        domain="example.com",
        records={
            "A": ["203.0.113.10"],
            "TXT": ["v=spf1 include:_spf.example.com -all"],
            "MX": ["10 mail.example.com"],
        },
        ttls={"A": 3600, "TXT": 3600},
        spf_records=["v=spf1 include:_spf.example.com -all"],
        dnskey_records=["256 3 13 ..."],
        ds_records=["12345 8 2 ABCD"],
        dkim_records={"google": ["v=DKIM1; k=rsa; p=MIIB..."]},
        dmarc_records=["v=DMARC1; p=reject; rua=mailto:dmarc@example.com"],
    )

    parsed = parse(raw)

    assert parsed.has_spf is True
    assert parsed.spf_is_weak is False
    assert parsed.dmarc_policy == "reject"
    assert parsed.dkim_selectors_found == ["google"]
    assert parsed.dnssec_enabled is True
    assert parsed.caa_present is False


def test_parse_detects_weak_spf_and_duplicate() -> None:
    raw = DnsRawResponse(
        domain="example.com",
        records={"TXT": ["v=spf1 +all", "v=spf1 include:a.com -all"]},
        spf_records=["v=spf1 +all", "v=spf1 include:a.com -all"],
    )
    parsed = parse(raw)
    assert parsed.spf_is_weak is True
    assert parsed.spf_has_duplicate is True
