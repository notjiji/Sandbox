"""End-to-end product pipeline — architecture connectivity.

Internal path is real (API → scan orchestrator → plugins → findings → risk → AI
context → report pipeline → audit). External I/O is mocked: websites (httpx),
DNS, TLS sockets, and the LLM provider.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.ai.models import AIResponsePayload
from app.services.ai.provider import LLMResult
from tests.support import TEST_PASSWORD, login_headers, verify_website_asset_via_api

pytestmark = pytest.mark.integration

_EMAIL = "pipeline-e2e@example.com"
_SITE = "https://pipeline.example.com"


def _data(response, *, status: int = 200) -> dict:
    assert response.status_code == status, response.text
    body = response.json()
    assert body.get("success") is True, response.text
    return body["data"]


def _mock_httpx(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "TRACE":
            return httpx.Response(405, text="Method Not Allowed")
        if request.url.scheme == "http":
            return httpx.Response(301, headers={"location": f"{_SITE}/"})
        if request.url.path.rstrip("/").endswith((".json", "api-docs")):
            return httpx.Response(404, text="not found")
        return httpx.Response(
            200,
            headers={
                "server": "nginx/1.24",
                "content-type": "text/html",
                "set-cookie": "sessionid=e2e; Path=/",
            },
            text="<html>pipeline</html>",
        )

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            kwargs["verify"] = False
            super().__init__(**kwargs)

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)


def _mock_dns(monkeypatch) -> None:
    def fake_query(_resolver, domain: str, rdtype: str):
        if domain.startswith("_dmarc."):
            return (["v=DMARC1; p=none"], 3600, None)
        mapping = {
            "A": (["203.0.113.10"], 3600, None),
            "AAAA": ([], None, "no answer"),
            "MX": (["10 mail.pipeline.example.com"], 3600, None),
            "TXT": (["v=spf1 -all"], 3600, None),
            "NS": (["ns1.pipeline.example.com"], 86400, None),
            "SOA": (
                ["ns1.pipeline.example.com. hostmaster.pipeline.example.com. 1 7200 3600 1209600 3600"],
                3600,
                None,
            ),
        }
        return mapping.get(rdtype, ([], None, "no answer"))

    monkeypatch.setattr("app.plugins.dns.collector._query", fake_query)
    monkeypatch.setattr("app.plugins.dns.collector._query_dkim", lambda *_a, **_k: {})
    monkeypatch.setattr("app.plugins.dns.collector.fetch_crtsh_names", lambda _domain: [])
    monkeypatch.setattr("app.plugins.dns.collector._collect_resolver_snapshots", lambda *_a, **_k: [])
    monkeypatch.setattr("app.plugins.dns.collector._verify_http_takeovers", lambda *_a, **_k: [])
    monkeypatch.setattr("app.plugins.dns.collector.validate_dnssec", lambda *_a, **_k: (None, None))
    monkeypatch.setattr("app.plugins.dns.collector.count_spf_dns_lookups", lambda *_a, **_k: 0)
    monkeypatch.setattr("app.plugins.dns.collector._attempt_zone_transfer", lambda *_a, **_k: False)


def _mock_tls(monkeypatch) -> None:
    async def fake_collect_sync(host: str, port: int, _timeout: float) -> dict:
        return {
            "host": host,
            "port": port,
            "negotiated_cipher": "TLS_AES_128_GCM_SHA256",
            "accepted_ciphers": ["TLS_AES_128_GCM_SHA256"],
            "weak_ciphers_accepted": [],
            "protocol_probes": [],
        }

    monkeypatch.setattr("app.plugins.tls.collector.collect_sync", fake_collect_sync)


def _mock_llm(monkeypatch) -> list[str]:
    calls: list[str] = []

    def fake_complete(self, *, system_prompt: str, user_content: str) -> LLMResult:  # noqa: ARG001
        calls.append(user_content)
        return LLMResult(
            payload=AIResponsePayload(
                answer="Mocked LLM: the scan context was received and findings can be explained.",
                summary="Pipeline AI mock",
                confidence="high",
            ),
            model="mock-e2e",
            input_tokens=12,
            output_tokens=24,
        )

    monkeypatch.setattr("app.services.ai.provider.LLMProvider.complete", fake_complete)
    return calls


def test_product_pipeline_connects(client, db, monkeypatch) -> None:
    """Create user → org → project → asset → verify → scan → plugins → finding → risk → AI → report → audit."""
    _mock_httpx(monkeypatch)
    _mock_dns(monkeypatch)
    _mock_tls(monkeypatch)
    llm_calls = _mock_llm(monkeypatch)
    monkeypatch.setattr("app.auth.services.auth_service.generate_otp", lambda: "123456")

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": _EMAIL,
            "password": TEST_PASSWORD,
            "first_name": "Pipeline",
            "last_name": "Owner",
        },
    )
    _data(register, status=201)

    verify = client.post("/api/v1/auth/verify-email", json={"email": _EMAIL, "otp": "123456"})
    _data(verify)

    headers = login_headers(client, email=_EMAIL)

    org = _data(
        client.post("/api/v1/organizations", json={"name": "Pipeline Org"}, headers=headers),
        status=201,
    )
    org_headers = {**headers, "X-Organization-ID": org["id"]}

    project = _data(
        client.post("/api/v1/projects", json={"name": "Pipeline Project"}, headers=org_headers),
        status=201,
    )
    project_id = project["id"]

    asset = _data(
        client.post(
            f"/api/v1/projects/{project_id}/assets",
            json={
                "name": "Pipeline Site",
                "type": "website",
                "status": "active",
                "environment": "production",
                "criticality": "high",
                "metadata": {"url": _SITE},
            },
            headers=org_headers,
        ),
        status=201,
    )
    asset_id = asset["id"]

    verify_website_asset_via_api(
        client,
        project_id=project_id,
        asset_id=asset_id,
        headers=org_headers,
        method="http",
        monkeypatch=monkeypatch,
    )

    scan = _data(
        client.post(
            f"/api/v1/projects/{project_id}/assets/{asset_id}/scans",
            json={"scan_type": "quick"},
            headers=org_headers,
        ),
        status=201,
    )
    scan_id = scan["id"]

    ran = _data(
        client.post(
            f"/api/v1/projects/{project_id}/assets/{asset_id}/scans/{scan_id}/run",
            headers=org_headers,
        )
    )
    assert ran["status"] == "completed"
    plugin_names = {item["plugin_name"] for item in ran["plugin_runs"]}
    assert {"http_headers", "tls", "dns", "cookies"} <= plugin_names
    assert all(item["status"] == "completed" for item in ran["plugin_runs"])

    findings = _data(
        client.get(
            f"/api/v1/projects/{project_id}/assets/{asset_id}/findings",
            headers=org_headers,
        )
    )
    assert findings["total"] > 0
    codes = {item["finding_code"] for item in findings["items"]}
    assert "HTTP_NO_CSP" in codes
    assert any(item["plugin"] == "http_headers" for item in findings["items"])
    assert all(item["risk_score"] is not None for item in findings["items"])

    risk = _data(
        client.get(
            f"/api/v1/organizations/risk/assets/{asset_id}",
            headers=org_headers,
        )
    )
    assert risk["scanned"] is True
    assert risk["scan_id"] == scan_id
    assert risk["total_risk"] > 0
    assert risk["score"] < 100

    chat = _data(
        client.post(
            "/api/v1/organizations/ai/chat",
            json={
                "message": "Summarize this asset's scan findings.",
                "capability": "asset_summary",
                "project_id": project_id,
                "asset_id": asset_id,
                "scan_id": scan_id,
            },
            headers=org_headers,
        )
    )
    assert chat["model"] == "mock-e2e"
    assert chat["response"]["answer"].startswith("Mocked LLM")
    assert llm_calls
    assert "HTTP_NO_CSP" in llm_calls[0] or "http_headers" in llm_calls[0]

    report = _data(
        client.post(
            f"/api/v1/projects/{project_id}/assets/{asset_id}/reports",
            json={"report_type": "executive", "scan_id": scan_id, "generate": True},
            headers=org_headers,
        ),
        status=201,
    )
    assert report["status"] == "ready"
    assert report["asset_id"] == asset_id
    download = client.get(
        f"/api/v1/projects/{project_id}/assets/{asset_id}/reports/{report['id']}/download",
        headers=org_headers,
    )
    assert download.status_code == 200, download.text
    assert download.content.startswith(b"%PDF")

    audit = _data(client.get("/api/v1/audit-logs", headers=org_headers, params={"limit": 100}))
    actions = {item["action"] for item in audit["items"]}
    assert "org.create" in actions
    assert "project.create" in actions
    assert "asset.create" in actions
    assert "scan.create" in actions
    assert "scan.completed" in actions
    assert "report.create" in actions or "report.generate" in actions
    assert "ai.summary_generated" in actions

    integrity = _data(client.get("/api/v1/audit-logs/integrity", headers=org_headers))
    assert integrity["valid"] is True
    assert integrity["checked"] >= 1
