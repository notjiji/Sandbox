"""Staging acceptance — full product story against live Compose stack.

Requires Docker. Mirrors the deployment path:
  Local → CI → Staging → (this test) → Production

Exercises Celery workers, durable report storage, service restart, and audit trail.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILES = [
    "docker-compose.prod.yml",
    "docker-compose.staging.yml",
    "docker-compose.staging-acceptance.yml",
]
ENV_FILE = REPO_ROOT / ".env.staging.acceptance"

MOCK_TARGET_URL = os.environ.get("STAGING_MOCK_TARGET_URL", "http://mock-target.test")
STAGING_OTP = os.environ.get("STAGING_FIXED_OTP", "123456")
TEST_PASSWORD = "StagingAcceptance1!"
TEST_EMAIL = f"staging-acceptance-{uuid.uuid4().hex[:8]}@example.com"
POLL_TIMEOUT_SECONDS = int(os.environ.get("STAGING_POLL_TIMEOUT", "180"))
ACCEPTANCE_DB_PASSWORD = "staging-acceptance-postgres-password-32"
# Avoid clashing with other Compose stacks that may already bind :80.
ACCEPTANCE_HTTP_PORT = os.environ.get("STAGING_HTTP_PORT", "18080")

_ACCEPTANCE_SECRET_REPLACEMENTS = {
    "POSTGRES_PASSWORD=CHANGE-ME-staging-postgres-password-32chars": (
        f"POSTGRES_PASSWORD={ACCEPTANCE_DB_PASSWORD}"
    ),
    "SECRET_KEY=CHANGE-ME-staging-secret-key-minimum-32-characters": (
        "SECRET_KEY=staging-acceptance-secret-key-minimum-32-chars"
    ),
    "JWT_SECRET=CHANGE-ME-staging-jwt-secret-minimum-32-characters": (
        "JWT_SECRET=staging-acceptance-jwt-secret-minimum-32-chars"
    ),
}

ENV_BACKUP = REPO_ROOT / ".env.acceptance-backup"


def _set_env_var(content: str, key: str, value: str) -> str:
    pattern = rf"^{re.escape(key)}=.*$"
    if re.search(pattern, content, flags=re.MULTILINE):
        return re.sub(pattern, f"{key}={value}", content, count=1, flags=re.MULTILINE)
    return f"{content.rstrip()}\n{key}={value}\n"


def _ensure_acceptance_env() -> None:
    source = REPO_ROOT / ".env.staging.example"
    if not source.is_file():
        pytest.fail("missing .env.staging.example")
    content = source.read_text(encoding="utf-8")
    for old, new in _ACCEPTANCE_SECRET_REPLACEMENTS.items():
        content = content.replace(old, new)
    content = _set_env_var(content, "POSTGRES_PASSWORD", ACCEPTANCE_DB_PASSWORD)
    content = _set_env_var(content, "SECRET_KEY", "staging-acceptance-secret-key-minimum-32-chars")
    content = _set_env_var(content, "JWT_SECRET", "staging-acceptance-jwt-secret-minimum-32-chars")
    ENV_FILE.write_text(content, encoding="utf-8")

    compose_env = REPO_ROOT / ".env"
    if compose_env.is_file() and not ENV_BACKUP.is_file():
        shutil.copy(compose_env, ENV_BACKUP)
    compose_env.write_text(content, encoding="utf-8")


def _restore_acceptance_env() -> None:
    if ENV_BACKUP.is_file():
        shutil.copy(ENV_BACKUP, REPO_ROOT / ".env")
        ENV_BACKUP.unlink(missing_ok=True)


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _compose(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    if not (REPO_ROOT / ".env").is_file():
        pytest.fail("missing .env — call _ensure_acceptance_env() first")
    merged = os.environ.copy()
    if env:
        merged.update(env)

    cmd = ["docker", "compose", "--env-file", ".env"]
    for compose_file in COMPOSE_FILES:
        cmd.extend(["-f", str(REPO_ROOT / compose_file)])
    project = merged.get("COMPOSE_PROJECT_NAME")
    if project:
        cmd.extend(["-p", project])
    cmd.extend(args)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
        env=merged,
    )


def _wait_http_ok(url: str, *, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
            last_error = f"status {response.status_code}"
        except httpx.HTTPError as exc:
            last_error = str(exc)
        time.sleep(2)
    pytest.fail(f"Timed out waiting for {url}: {last_error}")


def _wait_backend_ready(*, timeout: int = 120, compose_env: dict[str, str] | None = None) -> None:
    deadline = time.time() + timeout
    script = (
        "import urllib.request; "
        "r=urllib.request.urlopen('http://127.0.0.1:8000/health/ready'); "
        "exit(0 if r.status == 200 else 1)"
    )
    while time.time() < deadline:
        result = _compose("exec", "-T", "backend", "python", "-c", script, env=compose_env)
        if result.returncode == 0:
            return
        time.sleep(2)
    pytest.fail(f"backend not ready\n{result.stdout}\n{result.stderr}")


def _wait_celery_worker_ready(*, timeout: int = 180, compose_env: dict[str, str] | None = None) -> None:
    deadline = time.time() + timeout
    result = None
    while time.time() < deadline:
        result = _compose(
            "exec",
            "-T",
            "celery-worker",
            "python",
            "-m",
            "app.workers.health",
            "worker",
            env=compose_env,
        )
        if result.returncode == 0:
            return
        time.sleep(3)
    pytest.fail(
        f"celery-worker not ready\n{(result.stdout if result else '')}\n{(result.stderr if result else '')}"
    )


def _set_mock_verification_token(token: str, *, compose_env: dict[str, str] | None = None) -> None:
    result = _compose(
        "exec",
        "-T",
        "mock-target",
        "sh",
        "-c",
        f"mkdir -p /data && printf '%s' '{token}' > /data/verification-token.txt",
        env=compose_env,
    )
    if result.returncode != 0:
        pytest.fail(f"failed to set mock verification token\n{result.stdout}\n{result.stderr}")


class StagingClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)
        self.headers: dict[str, str] = {}

    def close(self) -> None:
        self.client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        expected: int = 200,
        json: dict | None = None,
        params: dict | None = None,
        raw: bool = False,
    ):
        response = self.client.request(
            method,
            path,
            json=json,
            params=params,
            headers=self.headers,
        )
        if raw:
            assert response.status_code == expected, response.text
            return response
        assert response.status_code == expected, response.text
        body = response.json()
        assert body.get("success") is True, response.text
        return body["data"]

    def login(self, *, email: str, password: str) -> None:
        response = self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200, response.text
        token = response.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    def with_org(self, org_id: str) -> None:
        self.headers = {**self.headers, "X-Organization-ID": org_id}


def _poll_until(
    fetch,
    *,
    label: str,
    predicate,
    timeout: int = POLL_TIMEOUT_SECONDS,
):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = fetch()
        if predicate(last):
            return last
        time.sleep(2)
    pytest.fail(f"Timed out waiting for {label}: last={last}")


def _run_product_story(api: StagingClient, *, compose_env: dict[str, str] | None = None) -> dict:
    """Register through audit trail; return handles for restart checks."""
    api.request(
        "POST",
        "/auth/register",
        expected=201,
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "first_name": "Staging",
            "last_name": "Acceptance",
        },
    )
    api.request(
        "POST",
        "/auth/verify-email",
        json={"email": TEST_EMAIL, "otp": STAGING_OTP},
    )
    api.login(email=TEST_EMAIL, password=TEST_PASSWORD)

    org = api.request("POST", "/organizations", expected=201, json={"name": "Staging Org"})
    api.with_org(org["id"])

    project = api.request("POST", "/projects", expected=201, json={"name": "Staging Project"})
    project_id = project["id"]

    asset = api.request(
        "POST",
        f"/projects/{project_id}/assets",
        expected=201,
        json={
            "name": "Staging Target",
            "type": "website",
            "status": "active",
            "environment": "staging",
            "criticality": "high",
            "metadata": {"url": MOCK_TARGET_URL},
        },
    )
    asset_id = asset["id"]

    challenge = api.request(
        "POST",
        f"/projects/{project_id}/assets/{asset_id}/verification/challenge",
        json={"method": "http"},
    )
    assert challenge["status"] == "pending"
    token = challenge["challenge_token"]
    assert token
    _set_mock_verification_token(token, compose_env=compose_env)

    verified = api.request(
        "POST",
        f"/projects/{project_id}/assets/{asset_id}/verification/verify",
    )
    assert verified["status"] == "verified"

    scan = api.request(
        "POST",
        f"/projects/{project_id}/assets/{asset_id}/scans",
        expected=201,
        json={"scan_type": "quick"},
    )
    scan_id = scan["id"]

    queued = api.request(
        "POST",
        f"/projects/{project_id}/assets/{asset_id}/scans/{scan_id}/run",
    )
    assert queued["status"] in {"queued", "running", "completed"}

    def fetch_scan():
        return api.request(
            "GET",
            f"/projects/{project_id}/assets/{asset_id}/scans/{scan_id}",
        )

    completed = _poll_until(
        fetch_scan,
        label="scan completion",
        predicate=lambda data: data["status"] == "completed",
    )
    plugin_runs = completed.get("plugin_runs", [])
    plugin_names = {item["plugin_name"] for item in plugin_runs}
    assert completed["status"] == "completed"
    assert {"http_headers", "tls", "dns", "cookies"} <= plugin_names
    assert any(item["status"] == "completed" for item in plugin_runs), plugin_runs

    findings = api.request(
        "GET",
        f"/projects/{project_id}/assets/{asset_id}/findings",
    )
    assert findings["total"] > 0

    risk = api.request("GET", f"/organizations/risk/assets/{asset_id}")
    assert risk["scanned"] is True
    assert risk["scan_id"] == scan_id
    assert risk["total_risk"] > 0

    dashboard = api.request("GET", "/organizations/current/dashboard/overview")
    findings_total = sum(dashboard["findings"].values())
    assert findings_total > 0
    assert dashboard["assets"]["total"] >= 1
    assert dashboard["last_scan"]["status"] in {"completed", "running", "queued", None} or dashboard["scanned_assets"] >= 1

    chat = api.request(
        "POST",
        "/organizations/ai/chat",
        json={
            "message": "Summarize findings for staging acceptance.",
            "capability": "asset_summary",
            "project_id": project_id,
            "asset_id": asset_id,
            "scan_id": scan_id,
        },
    )
    assert chat["model"] in {"offline", "mock-e2e"} or chat["response"]["answer"]

    report = api.request(
        "POST",
        f"/projects/{project_id}/assets/{asset_id}/reports",
        expected=201,
        json={"report_type": "executive", "scan_id": scan_id, "generate": True},
    )
    report_id = report["id"]

    def fetch_report():
        return api.request(
            "GET",
            f"/projects/{project_id}/assets/{asset_id}/reports/{report_id}",
        )

    ready = _poll_until(
        fetch_report,
        label="report generation",
        predicate=lambda data: data["status"] == "ready",
    )
    assert ready["file_url"]

    download = api.request(
        "GET",
        f"/projects/{project_id}/assets/{asset_id}/reports/{report_id}/download",
        raw=True,
    )
    pdf_bytes = download.content
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500

    audit = api.request("GET", "/audit-logs", params={"limit": 100})
    actions = {item["action"] for item in audit["items"]}
    for action in (
        "org.create",
        "project.create",
        "asset.create",
        "scan.create",
        "scan.completed",
    ):
        assert action in actions
    assert "report.create" in actions or "report.generate" in actions

    integrity = api.request("GET", "/audit-logs/integrity")
    assert integrity["valid"] is True
    assert integrity["checked"] >= 1

    export = api.request("GET", "/audit-logs/export", params={"format": "csv"}, raw=True)
    assert export.status_code == 200
    assert b"action" in export.content.lower()

    return {
        "project_id": project_id,
        "asset_id": asset_id,
        "report_id": report_id,
        "pdf_bytes": pdf_bytes,
    }


@pytest.mark.integration
@pytest.mark.skipif(not _docker_available(), reason="Docker not available")
def test_staging_acceptance_full_workflow() -> None:
    """Full staging product story including PDF retrieval after service restart."""
    _ensure_acceptance_env()
    project_name = f"sandbox-staging-acc-{uuid.uuid4().hex[:8]}"
    base_url = f"http://localhost:{ACCEPTANCE_HTTP_PORT}/api/v1"
    compose_env = {
        "COMPOSE_PROJECT_NAME": project_name,
        "NGINX_HTTP_PORT": ACCEPTANCE_HTTP_PORT,
    }
    _compose("down", "-v", "--remove-orphans", env=compose_env)

    try:
        infra = _compose("up", "-d", "postgres", "redis", "--wait", env=compose_env)
        if infra.returncode != 0:
            pytest.fail(f"postgres/redis up failed\n{infra.stdout}\n{infra.stderr}")

        migrate = _compose("up", "--abort-on-container-exit", "--exit-code-from", "migrate", "migrate", env=compose_env)
        if migrate.returncode != 0:
            pytest.fail(f"migrate failed\n{migrate.stdout}\n{migrate.stderr}")

        up = _compose(
            "up",
            "-d",
            "--build",
            "backend",
            "celery-worker",
            "celery-beat",
            "frontend",
            "nginx",
            "mock-target",
            "backup",
            env=compose_env,
        )
        if up.returncode != 0:
            pytest.fail(f"stack up failed\n{up.stdout}\n{up.stderr}")

        _wait_http_ok(f"http://localhost:{ACCEPTANCE_HTTP_PORT}/")
        _wait_backend_ready(compose_env=compose_env)
        _wait_celery_worker_ready(compose_env=compose_env)

        api = StagingClient(base_url)
        try:
            context = _run_product_story(api, compose_env=compose_env)
        except Exception as exc:
            service_logs = _compose(
                "logs",
                "backend",
                "celery-worker",
                "--tail",
                "150",
                env=compose_env,
            )
            pytest.fail(f"{exc}\n\n--- compose logs ---\n{service_logs.stdout}\n{service_logs.stderr}")
        finally:
            api.close()

        restart = _compose("restart", "backend", "celery-worker", env=compose_env)
        if restart.returncode != 0:
            pytest.fail(f"restart failed\n{restart.stdout}\n{restart.stderr}")

        _wait_backend_ready(timeout=180, compose_env=compose_env)
        _wait_celery_worker_ready(timeout=180, compose_env=compose_env)

        api = StagingClient(base_url)
        try:
            api.login(email=TEST_EMAIL, password=TEST_PASSWORD)
            orgs = api.request("GET", "/organizations/me")
            org_id = orgs["items"][0]["id"]
            api.with_org(org_id)

            redownload = api.request(
                "GET",
                (
                    f"/projects/{context['project_id']}/assets/{context['asset_id']}"
                    f"/reports/{context['report_id']}/download"
                ),
                raw=True,
            )
            assert redownload.content.startswith(b"%PDF")
            assert len(redownload.content) >= len(context["pdf_bytes"]) * 0.9

            report = api.request(
                "GET",
                f"/projects/{context['project_id']}/assets/{context['asset_id']}/reports/{context['report_id']}",
            )
            assert report["status"] == "ready"
            assert report["file_url"]

            integrity = api.request("GET", "/audit-logs/integrity")
            assert integrity["valid"] is True
        finally:
            api.close()
    finally:
        _compose("down", "-v", "--remove-orphans", env=compose_env)
        _restore_acceptance_env()


def test_staging_fixed_otp_setting(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("STAGING_FIXED_OTP", "654321")
    from app.core.config import get_settings
    from app.core.security import generate_otp

    get_settings.cache_clear()
    assert generate_otp() == "654321"
    get_settings.cache_clear()
