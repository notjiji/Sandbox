"""JWT and session security tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import ACCESS_TOKEN_TYPE
from tests.support import TEST_PASSWORD, create_verified_user

pytestmark = pytest.mark.integration


def _login(client, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _me(client, token: str, extra_headers: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"}
    if extra_headers:
        headers.update(extra_headers)
    return client.get("/api/v1/users/me", headers=headers)


def test_expired_access_token_is_rejected(client, db) -> None:
    user = create_verified_user(db, email="jwt-expired@example.com")
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "organization_id": "",
            "role": "",
            "type": ACCESS_TOKEN_TYPE,
            "exp": datetime.now(UTC) - timedelta(seconds=30),
            "iat": datetime.now(UTC) - timedelta(hours=1),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = _me(client, token)
    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_invalid_signature_token_is_rejected(client, db) -> None:
    user = create_verified_user(db, email="jwt-invalid@example.com")
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "organization_id": "",
            "role": "",
            "type": ACCESS_TOKEN_TYPE,
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
        },
        "wrong-secret-key-at-least-thirty-two-characters",
        algorithm=settings.JWT_ALGORITHM,
    )

    response = _me(client, token)
    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_malformed_access_token_is_rejected(client, db) -> None:
    create_verified_user(db, email="jwt-malformed@example.com")

    for raw in ("not-a-jwt", "aaa.bbb.ccc", "", "only-two.parts"):
        response = _me(client, raw)
        assert response.status_code == 401, response.text
        assert response.json()["error"]["code"] == "UNAUTHORIZED"

    missing_bearer = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Token abc"},
    )
    assert missing_bearer.status_code == 401


def test_refresh_token_is_invalidated_after_rotation_and_logout(client, db) -> None:
    create_verified_user(db, email="jwt-refresh@example.com")
    first = _login(client, "jwt-refresh@example.com")
    old_refresh = first["refresh_token"]

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200, rotated.text
    new_tokens = rotated.json()["data"]
    assert new_tokens["refresh_token"] != old_refresh

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401, replay.text
    assert replay.json()["error"]["code"] == "UNAUTHORIZED"

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert logout.status_code == 200, logout.text

    after_logout = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert after_logout.status_code == 401, after_logout.text


def test_session_mismatch_is_rejected(client, db) -> None:
    create_verified_user(db, email="jwt-session-a@example.com")
    create_verified_user(db, email="jwt-session-b@example.com")
    session_a = _login(client, "jwt-session-a@example.com")
    session_b = _login(client, "jwt-session-b@example.com")

    headers_a = {
        "Authorization": f"Bearer {session_a['access_token']}",
        "X-Session-ID": session_b["session_id"],
    }
    mismatch = client.post("/api/v1/auth/sessions/revoke-others", headers=headers_a)
    assert mismatch.status_code == 404, mismatch.text

    other_session = client.delete(
        f"/api/v1/auth/sessions/{session_b['session_id']}",
        headers={
            "Authorization": f"Bearer {session_a['access_token']}",
            "X-Session-ID": session_a["session_id"],
        },
    )
    assert other_session.status_code == 404, other_session.text

    malformed = client.post(
        "/api/v1/auth/sessions/revoke-others",
        headers={
            "Authorization": f"Bearer {session_a['access_token']}",
            "X-Session-ID": "not-a-uuid",
        },
    )
    assert malformed.status_code == 401, malformed.text

    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": session_a["refresh_token"]},
    )
    assert rotated.status_code == 200, rotated.text
    stale = client.post(
        "/api/v1/auth/sessions/revoke-others",
        headers={
            "Authorization": f"Bearer {rotated.json()['data']['access_token']}",
            "X-Session-ID": session_a["session_id"],
        },
    )
    assert stale.status_code == 404, stale.text
