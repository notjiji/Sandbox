"""Authentication API and service tests."""

from __future__ import annotations

import pytest

from app.auth.services import auth_service
from app.users.repositories.user_repository import get_user_by_email
from tests.support import TEST_PASSWORD, create_verified_user, login_headers

pytestmark = pytest.mark.integration


def test_register_verify_login_and_refresh(client, db, monkeypatch) -> None:
    monkeypatch.setattr("app.auth.services.auth_service.generate_otp", lambda: "123456")

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": TEST_PASSWORD,
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["success"] is True
    assert register_body["data"]["email"] == "newuser@example.com"
    assert "meta" in register_body
    assert register_body["meta"]["request_id"]

    verify_response = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "newuser@example.com", "otp": "123456"},
    )
    assert verify_response.status_code == 200

    user = get_user_by_email(db, "newuser@example.com")
    assert user is not None
    assert user.is_verified is True

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "newuser@example.com", "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["success"] is True
    tokens = login_body["data"]
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert refresh_body["success"] is True
    assert refresh_body["data"]["access_token"]


def test_login_rejects_invalid_credentials(client, db) -> None:
    create_verified_user(db, email="known@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "known@example.com", "password": "WrongPassword1!"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_protected_route_requires_authentication(client) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_authenticated_user_can_read_profile(client, db) -> None:
    create_verified_user(db, email="profile@example.com")
    headers = login_headers(client, email="profile@example.com")

    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "profile@example.com"


def test_logout_revokes_refresh_token(client, db) -> None:
    create_verified_user(db, email="logout@example.com")
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": TEST_PASSWORD},
    )
    tokens = login_response.json()["data"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_response.status_code == 200

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401
