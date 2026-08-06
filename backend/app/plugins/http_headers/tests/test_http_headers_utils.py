from app.plugins.http_headers.utils import analyze_csp, analyze_hsts, find_mixed_content


def test_analyze_csp_detects_unsafe() -> None:
    unsafe_inline, unsafe_eval, wildcard = analyze_csp("default-src 'self' 'unsafe-inline' *")
    assert unsafe_inline is True
    assert wildcard is True


def test_analyze_hsts_weak_max_age() -> None:
    max_age, subdomains, preload, is_weak = analyze_hsts("max-age=86400")
    assert max_age == 86400
    assert is_weak is True


def test_find_mixed_content() -> None:
    body = '<img src="http://example.com/a.png">'
    urls = find_mixed_content(body, is_https=True)
    assert len(urls) == 1
