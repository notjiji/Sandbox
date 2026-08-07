from app.plugins.dns.crtsh import extract_dkim_selectors, subdomains_from_ct


def test_extract_dkim_selectors_from_ct_names() -> None:
    names = ["google._domainkey.example.com", "www.example.com"]
    assert extract_dkim_selectors(names, "example.com") == ["google"]


def test_subdomains_from_ct_filters_apex() -> None:
    names = ["example.com", "api.example.com", "staging.example.com"]
    assert subdomains_from_ct(names, "example.com") == ["api", "staging"]
