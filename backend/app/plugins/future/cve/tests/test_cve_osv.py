from app.plugins.future.cve.osv import hints_from_http_headers, query_osv


def test_hints_from_http_headers_parses_server() -> None:
    hints = hints_from_http_headers({"server": "nginx/1.18.0"})
    assert hints[0].product == "nginx"
    assert hints[0].version == "1.18.0"


def test_query_osv_handles_network_failure(monkeypatch) -> None:
    monkeypatch.setattr("app.plugins.future.cve.osv.urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")))
    assert query_osv("nginx", "1.18.0", "Debian") == []
