"""Patterns for admin panels, debug folders, and other sensitive paths."""

from __future__ import annotations

from app.plugins.robots.schemas import MatchedSensitivePath, RobotsPathRule

PATH_CATEGORIES: list[tuple[str, tuple[str, ...]]] = [
    (
        "admin",
        (
            "/admin",
            "/administrator",
            "/wp-admin",
            "/backend",
            "/manage",
            "/manager",
            "/dashboard",
            "/cpanel",
            "/phpmyadmin",
            "/controlpanel",
            "/cms",
        ),
    ),
    (
        "debug",
        (
            "/debug",
            "/test",
            "/testing",
            "/dev",
            "/trace",
            "/console",
            "/phpinfo",
            "/.env",
            "/swagger",
            "/api-docs",
            "/actuator",
            "/elmah",
            "/error",
        ),
    ),
    (
        "sensitive",
        (
            "/private",
            "/internal",
            "/backup",
            "/backups",
            "/config",
            "/staging",
            "/secret",
            "/tmp",
            "/uploads",
            "/.git",
            "/api/internal",
            "/database",
            "/logs",
            "/shell",
        ),
    ),
]


def _normalize_path(path: str) -> str:
    cleaned = path.strip().lower()
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return cleaned


def classify_path(path: str) -> list[tuple[str, str]]:
    normalized = _normalize_path(path)
    matches: list[tuple[str, str]] = []
    for category, patterns in PATH_CATEGORIES:
        for pattern in patterns:
            if pattern in normalized:
                matches.append((category, pattern))
                break
    return matches


def scan_rules(rules: list[RobotsPathRule]) -> list[MatchedSensitivePath]:
    matched: list[MatchedSensitivePath] = []
    seen: set[tuple[str, str, str]] = set()
    for rule in rules:
        for category, pattern in classify_path(rule.path):
            key = (rule.path, category, rule.directive)
            if key in seen:
                continue
            seen.add(key)
            matched.append(
                MatchedSensitivePath(
                    path=rule.path,
                    category=category,
                    directive=rule.directive,
                    user_agent=rule.user_agent,
                    matched_pattern=pattern,
                )
            )
    return matched


def unique_paths_by_category(
    matched: list[MatchedSensitivePath],
) -> tuple[list[str], list[str], list[str]]:
    admin: list[str] = []
    debug: list[str] = []
    sensitive: list[str] = []
    for item in matched:
        if item.category == "admin" and item.path not in admin:
            admin.append(item.path)
        elif item.category == "debug" and item.path not in debug:
            debug.append(item.path)
        elif item.category == "sensitive" and item.path not in sensitive:
            sensitive.append(item.path)
    return admin, debug, sensitive
