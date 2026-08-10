DEFAULT_ORGANIZATION_SETTINGS: dict = {
    "language": "en",
    "notifications": {
        "email_enabled": True,
        "weekly_reports": True,
        "scan_complete": True,
        "critical_findings": True,
    },
    "security": {
        "mfa_policy": "optional",
        "password_min_length": 12,
        "session_timeout_minutes": 480,
    },
    "branding": {
        "primary_color": "#7c3aed",
        "contact_email": None,
        "footer_text": None,
    },
}


def merge_organization_settings(current: dict | None) -> dict:
    base = {
        "language": DEFAULT_ORGANIZATION_SETTINGS["language"],
        "notifications": dict(DEFAULT_ORGANIZATION_SETTINGS["notifications"]),
        "security": dict(DEFAULT_ORGANIZATION_SETTINGS["security"]),
        "branding": dict(DEFAULT_ORGANIZATION_SETTINGS["branding"]),
    }
    if not current:
        return base

    if language := current.get("language"):
        base["language"] = language

    if notifications := current.get("notifications"):
        if isinstance(notifications, dict):
            base["notifications"].update(notifications)

    if security := current.get("security"):
        if isinstance(security, dict):
            base["security"].update(security)

    if branding := current.get("branding"):
        if isinstance(branding, dict):
            base["branding"].update(branding)

    return base
