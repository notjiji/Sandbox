"""Production public-edge security boundary."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.middleware.production_boundary import is_blocked_public_operator_path

REPO_ROOT = Path(__file__).resolve().parents[2]
NGINX_PROD = REPO_ROOT / "infrastructure" / "nginx" / "nginx.prod.conf"


@pytest.mark.parametrize(
    "path",
    ["/docs", "/docs/", "/redoc", "/redoc/", "/openapi.json", "/openapi.yaml"],
)
def test_blocked_operator_paths(path: str) -> None:
    assert is_blocked_public_operator_path(path)


@pytest.mark.parametrize("path", ["/metrics", "/api/v1/health", "/health", "/"])
def test_allowed_operator_paths(path: str) -> None:
    assert not is_blocked_public_operator_path(path)


def test_nginx_prod_blocks_public_operator_endpoints() -> None:
    content = NGINX_PROD.read_text(encoding="utf-8")
    for marker in ("/metrics", "/openapi.json", "/docs", "/redoc"):
        assert marker in content
    assert content.count("return 404") >= 4


@pytest.fixture
def production_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("POSTGRES_PASSWORD", "prod-db-credential-x7k9m2n4p8q1r5t3")
    monkeypatch.setenv("SECRET_KEY", "production-test-secret-key-minimum-32-chars")
    monkeypatch.setenv("JWT_SECRET", "production-test-jwt-secret-minimum-32-chars")
    monkeypatch.setenv("RESEND_API_KEY", "re_production_test_email_api_key_32chars")
    monkeypatch.setenv("BACKUP_ENCRYPTION_PASSPHRASE", "production-backup-passphrase-minimum-32-chars")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")
    monkeypatch.setenv("PUBLIC_API_URL", "https://app.example.com/api/v1")
    monkeypatch.setenv("SCAN_RUN_INLINE", "false")
    monkeypatch.setenv("REPORT_RUN_INLINE", "false")
    monkeypatch.setenv("AI_ENABLED", "false")
    get_settings.cache_clear()
    import app.main as main_module

    importlib.reload(main_module)
    with TestClient(main_module.app) as client:
        yield client
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("POSTGRES_PASSWORD", "changeme-in-dev-only-32chars")
    get_settings.cache_clear()
    importlib.reload(main_module)


def test_production_backend_blocks_openapi_and_docs(production_client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        response = production_client.get(path)
        assert response.status_code == 404, path


def test_production_backend_keeps_internal_prometheus_metrics(production_client: TestClient) -> None:
    response = production_client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_production_backend_keeps_api_public(production_client: TestClient) -> None:
    response = production_client.get("/health")
    assert response.status_code == 200
