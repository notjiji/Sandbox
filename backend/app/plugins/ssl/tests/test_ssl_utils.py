from app.plugins.ssl.utils import hostname_matches_pattern, resolve_host_port


def test_resolve_host_port() -> None:
    assert resolve_host_port("example.com") == ("example.com", 443)
    assert resolve_host_port("https://example.com:8443/path") == ("example.com", 8443)


def test_hostname_matches_pattern() -> None:
    assert hostname_matches_pattern("www.example.com", "*.example.com") is True
    assert hostname_matches_pattern("example.com", "*.example.com") is True
    assert hostname_matches_pattern("other.com", "*.example.com") is False
