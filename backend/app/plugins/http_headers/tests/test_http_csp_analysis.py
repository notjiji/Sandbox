from app.plugins.http_headers.csp_analysis import analyze_csp_deep


def test_analyze_csp_deep_flags_broad_sources() -> None:
    csp = "default-src 'self'; script-src https: data: blob:"
    unsafe_inline, unsafe_eval, wildcard, data, blob, broad_https = analyze_csp_deep(csp)
    assert unsafe_inline is False
    assert data is True
    assert blob is True
    assert broad_https is True
