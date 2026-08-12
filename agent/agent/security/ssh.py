from __future__ import annotations

from typing import Any

from agent.collectors._util import read_text


def collect() -> dict | None:
    raw = read_text("/etc/ssh/sshd_config")
    if raw is None:
        return None
    permit_root = None
    password_auth = None
    port = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0].lower(), parts[1].strip().lower()
        if key == "permitrootlogin":
            permit_root = value not in {
                "no",
                "prohibit-password",
                "without-password",
                "forced-commands-only",
            }
        elif key == "passwordauthentication":
            password_auth = value == "yes"
        elif key == "port":
            try:
                port = int(value)
            except ValueError:
                port = None
    result: dict[str, Any] = {
        "permit_root_login": permit_root,
        "password_authentication": password_auth,
        "port": port,
    }
    return result
