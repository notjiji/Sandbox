"""One-shot architecture migration helper. Safe to delete after running."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

ROUTE_SOURCES = {
    "auth": APP / "api" / "v1" / "auth" / "routes.py",
    "users": APP / "api" / "v1" / "users" / "routes.py",
    "organizations": APP / "api" / "v1" / "organizations" / "routes.py",
    "members": APP / "api" / "v1" / "members" / "routes.py",
    "projects": APP / "api" / "v1" / "projects" / "routes.py",
    "assets": APP / "api" / "v1" / "assets" / "routes.py",
    "scans": APP / "api" / "v1" / "scans" / "routes.py",
    "findings": APP / "api" / "v1" / "findings" / "routes.py",
    "reports": APP / "api" / "v1" / "reports" / "routes.py",
}

REPOSITORY_MOVES: dict[str, list[tuple[str, str]]] = {
    "assets": [("repository.py", "asset_repository.py")],
    "audit": [("repository.py", "audit_repository.py")],
    "findings": [("repository.py", "finding_repository.py")],
    "members": [("repository.py", "member_repository.py")],
    "organizations": [
        ("repository.py", "organization_repository.py"),
        ("invite_repository.py", "invite_repository.py"),
    ],
    "projects": [("repository.py", "project_repository.py")],
    "reports": [("repository.py", "report_repository.py")],
    "scans": [("repository.py", "scan_repository.py")],
    "users": [("repository.py", "user_repository.py")],
    "auth": [
        ("email_verification_repository.py", "email_verification_repository.py"),
        ("password_reset_repository.py", "password_reset_repository.py"),
        ("refresh_token_repository.py", "refresh_token_repository.py"),
    ],
}

IMPORT_REPLACEMENTS = [
    ("from app.assets.repository import", "from app.assets.repositories.asset_repository import"),
    ("from app.audit.repository import", "from app.audit.repositories.audit_repository import"),
    ("from app.findings.repository import", "from app.findings.repositories.finding_repository import"),
    ("from app.members.repository import", "from app.members.repositories.member_repository import"),
    ("from app.organizations.repository import", "from app.organizations.repositories.organization_repository import"),
    ("from app.organizations.invite_repository import", "from app.organizations.repositories.invite_repository import"),
    ("from app.projects.repository import", "from app.projects.repositories.project_repository import"),
    ("from app.reports.repository import", "from app.reports.repositories.report_repository import"),
    ("from app.scans.repository import", "from app.scans.repositories.scan_repository import"),
    ("from app.users.repository import", "from app.users.repositories.user_repository import"),
    ("from app.auth.email_verification_repository import", "from app.auth.repositories.email_verification_repository import"),
    ("from app.auth.password_reset_repository import", "from app.auth.repositories.password_reset_repository import"),
    ("from app.auth.refresh_token_repository import", "from app.auth.repositories.refresh_token_repository import"),
    ("from app.api.v1.assets import router as assets_router", "from app.assets.router import router as assets_router"),
    ("from app.api.v1.findings import router as findings_router", "from app.findings.router import router as findings_router"),
    ("from app.api.v1.reports import router as reports_router", "from app.reports.router import router as reports_router"),
    ("from app.api.v1.scans import router as scans_router", "from app.scans.router import router as scans_router"),
    ("from app.services.health import get_health", "from app.core.health import get_health"),
]


def copy_feature_routers() -> None:
    for feature, src in ROUTE_SOURCES.items():
        if not src.exists():
            continue
        dest = APP / feature / "router.py"
        content = src.read_text(encoding="utf-8")
        if feature == "projects":
            content = content.replace(
                "from app.api.v1.assets import router as assets_router",
                "from app.assets.router import router as assets_router",
            ).replace(
                "from app.api.v1.findings import router as findings_router",
                "from app.findings.router import router as findings_router",
            ).replace(
                "from app.api.v1.reports import router as reports_router",
                "from app.reports.router import router as reports_router",
            ).replace(
                "from app.api.v1.scans import router as scans_router",
                "from app.scans.router import router as scans_router",
            )
        dest.write_text(content, encoding="utf-8")
        print(f"copied router -> {dest.relative_to(ROOT)}")


def move_repositories() -> None:
    for feature, moves in REPOSITORY_MOVES.items():
        repos_dir = APP / feature / "repositories"
        repos_dir.mkdir(parents=True, exist_ok=True)
        init = repos_dir / "__init__.py"
        if not init.exists():
            init.write_text('"""Feature repositories."""\n', encoding="utf-8")
        for src_name, dest_name in moves:
            src = APP / feature / src_name
            dest = repos_dir / dest_name
            if src.exists() and not dest.exists():
                shutil.move(str(src), str(dest))
                print(f"moved {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


def apply_import_replacements() -> None:
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in IMPORT_REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"updated imports in {path.relative_to(ROOT)}")


def main() -> None:
    copy_feature_routers()
    move_repositories()
    apply_import_replacements()
    print("migration steps complete")


if __name__ == "__main__":
    main()
