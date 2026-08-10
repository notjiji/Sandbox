"""Shared helpers for integration tests."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.assets.enums import AssetCriticality, AssetEnvironment, AssetStatus, AssetType
from app.assets.schemas import CreateAssetRequest
from app.assets.services import create_project_asset
from app.core.security import hash_password
from app.members.models import OrganizationMember
from app.organizations.schemas import CreateOrganizationRequest
from app.projects.schemas import CreateProjectRequest
from app.scans.enums import ScanType
from app.scans.schemas import CreateAssetScanRequest
from app.scans.services import scan_service
from app.users.models import User
from app.users.repositories.user_repository import create_user, mark_user_verified

TEST_PASSWORD = "TestPassword1!"


def create_verified_user(
    db: Session,
    *,
    email: str = "test@example.com",
    password: str = TEST_PASSWORD,
    first_name: str = "Test",
    last_name: str = "User",
) -> User:
    user = create_user(
        db,
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )
    mark_user_verified(db, user)
    db.commit()
    db.refresh(user)
    return user


def login_headers(client, *, email: str, password: str = TEST_PASSWORD) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    if data.get("session_id"):
        headers["X-Session-ID"] = data["session_id"]
    return headers


def bootstrap_org_context(
    db: Session,
    client,
    *,
    email: str = "owner@example.com",
    org_name: str = "Test Org",
    project_name: str = "Test Project",
) -> dict[str, Any]:
    create_verified_user(db, email=email)
    headers = login_headers(client, email=email)

    org_response = client.post(
        "/api/v1/organizations",
        json={"name": org_name},
        headers=headers,
    )
    assert org_response.status_code == 201, org_response.text
    org = org_response.json()["data"]
    org_headers = {**headers, "X-Organization-ID": org["id"]}

    project_response = client.post(
        "/api/v1/projects",
        json={"name": project_name},
        headers=org_headers,
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()["data"]

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == uuid.UUID(org["id"]),
            OrganizationMember.user_id
            == db.query(User).filter(User.email == email).first().id,
        )
        .one()
    )

    return {
        "email": email,
        "headers": headers,
        "org_headers": org_headers,
        "organization": org,
        "project": project,
        "membership": membership,
    }


def invite_and_accept_member(
    db: Session,
    client,
    owner_ctx: dict[str, Any],
    *,
    email: str,
    role: str = "viewer",
) -> dict[str, Any]:
    """Invite a user to the owner's org and return their authenticated org context."""
    create_verified_user(db, email=email)

    invite_response = client.post(
        "/api/v1/organizations/current/members",
        json={"email": email, "role": role},
        headers=owner_ctx["org_headers"],
    )
    assert invite_response.status_code == 201, invite_response.text

    member_headers = login_headers(client, email=email)
    accept_response = client.post(
        "/api/v1/organizations/current/members/accept",
        headers={**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]},
    )
    assert accept_response.status_code == 200, accept_response.text

    org_headers = {**member_headers, "X-Organization-ID": owner_ctx["organization"]["id"]}
    return {
        "email": email,
        "headers": member_headers,
        "org_headers": org_headers,
        "membership_id": accept_response.json()["data"]["membership_id"],
    }


def create_website_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    name: str = "Example Site",
    url: str = "https://example.com",
):
    return create_project_asset(
        db,
        membership,
        project_id=project_id,
        body=CreateAssetRequest(
            name=name,
            type=AssetType.WEBSITE,
            status=AssetStatus.ACTIVE,
            environment=AssetEnvironment.PRODUCTION,
            criticality=AssetCriticality.MEDIUM,
            metadata={"url": url},
        ),
    )


def create_pending_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
):
    return scan_service.create_asset_scan(
        db,
        membership,
        project_id=project_id,
        asset_id=asset_id,
        body=CreateAssetScanRequest(scan_type=ScanType.QUICK),
    )
