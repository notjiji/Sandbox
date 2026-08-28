"""Pytest fixtures for API and service integration tests."""

from __future__ import annotations

import os
from collections.abc import Generator

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configure environment before application imports.
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "sandbox_test")
os.environ.setdefault("POSTGRES_USER", "sandbox")
os.environ.setdefault("POSTGRES_PASSWORD", "changeme-in-dev-only-32chars")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-at-least-thirty-two-characters-long",
)
os.environ.setdefault(
    "JWT_SECRET",
    "test-jwt-secret-at-least-thirty-two-characters-long",
)
os.environ.setdefault("REDIS_URL", "memory://")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SCAN_RUN_INLINE", "true")
os.environ.setdefault("RESEND_API_KEY", "re_test_key")
os.environ.setdefault("RESEND_FROM", "test@example.com")

import tempfile

_report_storage_dir = tempfile.mkdtemp(prefix="sandbox-report-storage-")
os.environ.setdefault("REPORT_STORAGE_BACKEND", "local")
os.environ.setdefault("REPORT_STORAGE_PATH", _report_storage_dir)

from app.core.config import get_settings
from app.core.report_storage import reset_report_storage_cache

get_settings.cache_clear()
reset_report_storage_cache()


@pytest.fixture(autouse=True)
def _refresh_report_storage_cache() -> None:
    get_settings.cache_clear()
    reset_report_storage_cache()
    yield
    get_settings.cache_clear()
    reset_report_storage_cache()


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw) -> str:
    return "JSON"


@compiles(PGUUID, "sqlite")
def _compile_uuid_sqlite(_element, _compiler, **_kw) -> str:
    return "CHAR(36)"


def _import_models() -> None:
    import app.assets.models  # noqa: F401
    import app.audit.models  # noqa: F401
    import app.auth.models  # noqa: F401
    import app.findings.models  # noqa: F401
    import app.members.models  # noqa: F401
    import app.organizations.invites  # noqa: F401
    import app.organizations.models  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.reports.models  # noqa: F401
    import app.risk.models  # noqa: F401
    import app.scans.models  # noqa: F401
    import app.scans.schedule_models  # noqa: F401
    import app.assets.saved_filter_models  # noqa: F401
    import app.users.models  # noqa: F401
    import app.monitoring.models  # noqa: F401


_import_models()

from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.shared.db.base import Base  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autocommit=False, autoflush=False)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def _noop_auth_emails(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.auth.services.auth_service.send_verification_otp_email",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        "app.auth.services.auth_service.send_password_reset_email",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        "app.members.services.invite_service.send_organization_invite_email",
        lambda **_kwargs: None,
    )


@pytest.fixture(autouse=True)
def disable_rate_limiting() -> None:
    from app.core.rate_limit import limiter

    previous = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = previous


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch) -> fakeredis.FakeRedis:
    client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.core.redis._redis_client", client)
    monkeypatch.setattr("app.core.redis.get_redis_client", lambda: client)
    client.flushdb()
    yield client
    client.flushdb()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
