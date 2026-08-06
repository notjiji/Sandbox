import asyncio

import httpx

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.collector import collect


def test_collect_builds_raw_response_with_mock_transport(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "TRACE":
            return httpx.Response(405, text="Method Not Allowed")
        if request.url.scheme == "http":
            return httpx.Response(301, headers={"location": "https://example.com/"})
        return httpx.Response(
            200,
            headers={
                "server": "nginx",
                "content-type": "text/html",
                "set-cookie": "sessionid=abc; Path=/",
            },
            text="<html>ok</html>",
        )

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            kwargs["verify"] = False
            super().__init__(**kwargs)

    monkeypatch.setattr("app.plugins.http_headers.collector.httpx.AsyncClient", MockAsyncClient)

    raw = asyncio.run(
        collect(
            ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
            ScanOptions(timeout=5.0),
        )
    )

    assert raw.primary.status_code == 200
    assert raw.primary.headers["server"] == "nginx"
    assert len(raw.primary.cookies) == 1
    assert raw.http_probe is not None
    assert raw.http_probe.status_code == 301
    assert raw.trace_probe is not None
    assert raw.trace_probe.allowed is False
