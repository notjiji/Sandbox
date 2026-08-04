#!/usr/bin/env python3
"""Populate the database with demo organization, users, projects, assets, scans, and findings.

Usage (Docker):
    docker compose exec backend python scripts/seed_demo.py

Usage (local, from backend/):
    python scripts/seed_demo.py

Requires: alembic upgrade head (migrations 018+ for risk rules).
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.assets.enums import (
    AssetCriticality,
    AssetEnvironment,
    AssetStatus,
    AssetType,
)
from app.assets.repositories.asset_repository import (
    create_asset,
    replace_tags,
    upsert_metadata_entries,
)
from app.core.database import SessionLocal
from app.core.risk_engine.engine import risk_engine
from app.core.security import hash_password
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.repositories.finding_repository import create_finding
from app.members.enums import MemberStatus, OrganizationRole
from app.members.repositories.member_repository import (
    add_organization_member,
    get_membership,
)
from app.organizations.repositories.organization_repository import (
    create_organization,
    get_organization_by_slug,
)
from app.projects.repositories.project_repository import create_project
from app.risk.repositories.risk_repository import get_rule_for_finding
from app.scans.enums import ScanStatus, ScanType
from app.scans.lifecycle import transition_scan_status
from app.scans.repositories.scan_repository import create_scan
from app.users.repositories.user_repository import (
    create_user,
    get_user_by_email,
    mark_user_verified,
)
from scripts.demo_data import DEMO_ORG_SLUG, DEMO_PASSWORD, DEMO_USERS


def _rule_finding(
    db: Session,
    *,
    plugin: str,
    finding_code: str,
) -> tuple[FindingSeverity, float, str, str | None]:
    rule = get_rule_for_finding(db, plugin=plugin, finding_code=finding_code)
    if rule is None:
        raise RuntimeError(
            f"Risk rule {plugin}/{finding_code} not found. Run: alembic upgrade head"
        )
    return rule.severity, float(rule.score), rule.title, rule.description


def _complete_scan(db: Session, scan) -> None:
    """Walk scan through PENDING → QUEUED → RUNNING → COMPLETED."""
    base = datetime.now(UTC) - timedelta(hours=2)
    transition_scan_status(scan, status=ScanStatus.QUEUED, at=base)
    transition_scan_status(scan, status=ScanStatus.RUNNING, at=base + timedelta(minutes=1))
    transition_scan_status(scan, status=ScanStatus.COMPLETED, at=base + timedelta(minutes=5))
    db.add(scan)
    db.flush()


def _seed_demo(db: Session) -> None:
    owner_spec = DEMO_USERS[0]
    owner = get_user_by_email(db, owner_spec["email"])
    if owner is None:
        owner = create_user(
            db,
            email=owner_spec["email"],
            hashed_password=hash_password(DEMO_PASSWORD),
            first_name=owner_spec["first_name"],
            last_name=owner_spec["last_name"],
        )
        mark_user_verified(db, owner)

    org = get_organization_by_slug(db, DEMO_ORG_SLUG)
    if org is None:
        org = create_organization(
            db,
            name="Demo Corp",
            slug=DEMO_ORG_SLUG,
            description="Sample organization for demos, QA, and local development.",
            industry="Technology",
            website="https://demo-corp.com",
            country="US",
            timezone="America/New_York",
            created_by=owner.id,
        )

    for spec in DEMO_USERS:
        user = get_user_by_email(db, spec["email"])
        if user is None:
            user = create_user(
                db,
                email=spec["email"],
                hashed_password=hash_password(DEMO_PASSWORD),
                first_name=spec["first_name"],
                last_name=spec["last_name"],
            )
            mark_user_verified(db, user)
        if get_membership(db, organization_id=org.id, user_id=user.id) is None:
            add_organization_member(
                db,
                organization_id=org.id,
                user_id=user.id,
                role=OrganizationRole(spec["role"]),
                status=MemberStatus.ACTIVE,
                joined_at=datetime.now(UTC),
            )

    web_project = create_project(
        db,
        organization_id=org.id,
        name="Production Web Apps",
        slug="production-web",
        description="Customer-facing websites and APIs.",
        created_by=owner.id,
    )
    infra_project = create_project(
        db,
        organization_id=org.id,
        name="Cloud Infrastructure",
        slug="cloud-infra",
        description="Cloud accounts and storage buckets.",
        created_by=owner.id,
    )

    website = create_asset(
        db,
        organization_id=org.id,
        project_id=web_project.id,
        name="Demo Corp Website",
        type=AssetType.WEBSITE,
        description="Primary marketing site",
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.PRODUCTION,
        criticality=AssetCriticality.CRITICAL,
        owner="Platform Team",
        created_by=owner.id,
    )
    upsert_metadata_entries(
        db,
        asset_id=website.id,
        metadata={"url": "https://demo-corp.com"},
    )
    replace_tags(db, asset_id=website.id, tags=["production", "customer-facing"])

    domain = create_asset(
        db,
        organization_id=org.id,
        project_id=web_project.id,
        name="demo-corp.com",
        type=AssetType.DOMAIN,
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.PRODUCTION,
        criticality=AssetCriticality.HIGH,
        created_by=owner.id,
    )
    upsert_metadata_entries(db, asset_id=domain.id, metadata={"domain": "demo-corp.com"})

    public_ip = create_asset(
        db,
        organization_id=org.id,
        project_id=web_project.id,
        name="Website Public IP",
        type=AssetType.PUBLIC_IP,
        parent_id=website.id,
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.PRODUCTION,
        criticality=AssetCriticality.MEDIUM,
        created_by=owner.id,
    )
    upsert_metadata_entries(db, asset_id=public_ip.id, metadata={"address": "203.0.113.10"})

    api_asset = create_asset(
        db,
        organization_id=org.id,
        project_id=web_project.id,
        name="Public API Gateway",
        type=AssetType.API_ENDPOINT,
        description="REST API for mobile clients",
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.PRODUCTION,
        criticality=AssetCriticality.HIGH,
        owner="API Team",
        created_by=owner.id,
    )
    upsert_metadata_entries(
        db,
        asset_id=api_asset.id,
        metadata={"endpoint": "https://api.demo-corp.com/v1"},
    )
    replace_tags(db, asset_id=api_asset.id, tags=["api", "production"])

    legacy_server = create_asset(
        db,
        organization_id=org.id,
        project_id=web_project.id,
        name="Legacy App Server",
        type=AssetType.SERVER,
        description="Not yet scanned — shows unscanned asset risk state",
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.STAGING,
        criticality=AssetCriticality.MEDIUM,
        created_by=owner.id,
    )
    upsert_metadata_entries(
        db,
        asset_id=legacy_server.id,
        metadata={"hostname": "legacy-app-01.demo-corp.com", "os": "Ubuntu 22.04"},
    )

    cloud_account = create_asset(
        db,
        organization_id=org.id,
        project_id=infra_project.id,
        name="AWS Production",
        type=AssetType.CLOUD_ACCOUNT,
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.PRODUCTION,
        criticality=AssetCriticality.CRITICAL,
        created_by=owner.id,
    )
    upsert_metadata_entries(
        db,
        asset_id=cloud_account.id,
        metadata={"account_id": "123456789012"},
    )

    s3_bucket = create_asset(
        db,
        organization_id=org.id,
        project_id=infra_project.id,
        name="Application Logs Bucket",
        type=AssetType.S3_BUCKET,
        parent_id=cloud_account.id,
        status=AssetStatus.ACTIVE,
        environment=AssetEnvironment.PRODUCTION,
        criticality=AssetCriticality.MEDIUM,
        created_by=owner.id,
    )
    upsert_metadata_entries(
        db,
        asset_id=s3_bucket.id,
        metadata={"bucket": "demo-corp-app-logs"},
    )

    website_scan = create_scan(
        db,
        project_id=web_project.id,
        asset_id=website.id,
        scan_type=ScanType.FULL,
        created_by=owner.id,
    )
    _complete_scan(db, website_scan)

    api_scan = create_scan(
        db,
        project_id=web_project.id,
        asset_id=api_asset.id,
        scan_type=ScanType.QUICK,
        created_by=owner.id,
    )
    _complete_scan(db, api_scan)

    pending_scan = create_scan(
        db,
        project_id=web_project.id,
        asset_id=legacy_server.id,
        scan_type=ScanType.QUICK,
        created_by=owner.id,
    )
    transition_scan_status(pending_scan, status=ScanStatus.QUEUED)
    db.add(pending_scan)

    website_findings = [
        ("http_headers", "HTTP_NO_CSP"),
        ("http_headers", "HTTP_NO_HSTS"),
        ("ssl", "SSL_EXPIRED"),
        ("dns", "DNS_MISSING_SPF"),
        ("whois", "WHOIS_EXPIRING_SOON"),
    ]
    for plugin, code in website_findings:
        severity, score, title, description = _rule_finding(db, plugin=plugin, finding_code=code)
        create_finding(
            db,
            project_id=web_project.id,
            scan_id=website_scan.id,
            asset_id=website.id,
            plugin=plugin,
            finding_code=code,
            check_status="fail",
            title=title,
            description=description,
            severity=severity,
            risk_score=score,
            status=FindingStatus.OPEN,
            detected_at=website_scan.completed_at,
        )

    api_findings = [
        ("http_headers", "HTTP_NO_HSTS"),
        ("ssl", "SSL_TLS10_ENABLED"),
    ]
    for plugin, code in api_findings:
        severity, score, title, description = _rule_finding(db, plugin=plugin, finding_code=code)
        create_finding(
            db,
            project_id=web_project.id,
            scan_id=api_scan.id,
            asset_id=api_asset.id,
            plugin=plugin,
            finding_code=code,
            check_status="fail",
            title=title,
            description=description,
            severity=severity,
            risk_score=score,
            status=FindingStatus.OPEN,
            detected_at=api_scan.completed_at,
        )

    risk_engine.recalculate_after_scan(
        db,
        project_id=web_project.id,
        asset_id=website.id,
        scan_id=website_scan.id,
        organization_id=org.id,
    )
    risk_engine.recalculate_after_scan(
        db,
        project_id=web_project.id,
        asset_id=api_asset.id,
        scan_id=api_scan.id,
        organization_id=org.id,
    )
    risk_engine.calculate_project_risk(db, project_id=infra_project.id, store=True)

    db.commit()

    print("Demo data seeded successfully.")
    print()
    print("Organization : Demo Corp (slug: demo-corp)")
    print(f"Password (all) : {DEMO_PASSWORD}")
    print()
    print("Accounts:")
    for spec in DEMO_USERS:
        print(f"  - {spec['email']:<28} role={spec['role']}")
    print()
    print("Projects:")
    print("  - Production Web Apps (production-web) — 4 assets, 2 completed scans, 7 findings")
    print("  - Cloud Infrastructure (cloud-infra) — 2 assets, unscanned")
    print()
    print("See docs/demo-data.md for login notes and URLs to explore.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo data for Sandbox")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-seed even if demo organization already exists (not implemented — wipe DB first)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existing = get_organization_by_slug(db, DEMO_ORG_SLUG)
        if existing and not args.force:
            print(f"Demo organization '{DEMO_ORG_SLUG}' already exists — skipping seed.")
            print("See docs/demo-data.md for login credentials.")
            print("To re-seed from scratch: docker compose down -v && docker compose up -d && make migrate && make seed")
            return 0

        if existing and args.force:
            print("ERROR: --force re-seed is not supported. Reset the database volume first.")
            return 1

        _seed_demo(db)
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
