from __future__ import annotations

import glob
import shutil
from typing import Any

from agent.collectors._util import read_text, run

_CONFIG_PATHS = (
    "/etc/ssh/sshd_config",
    "/etc/ssh/sshd_config.d/*.conf",
)


def _truthy(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.strip().lower() in {"yes", "true", "1"}


def _root_login_enabled(raw: str | None) -> bool | None:
    if raw is None:
        return None
    value = raw.strip().lower()
    # Keys-only / restricted root is not treated as full root login for alerts.
    if value in {"no", "prohibit-password", "without-password", "forced-commands-only"}:
        return False
    if value in {"yes", "true", "1"}:
        return True
    return None


def _parse_sshd_t(output: str) -> dict[str, str]:
    directives: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        directives[parts[0].lower()] = parts[1].strip()
    return directives


def _parse_config_text(raw: str) -> dict[str, str]:
    """Last matching directive wins (OpenSSH effective behavior for most keys)."""
    directives: dict[str, str] = {}
    includes: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0].lower(), parts[1].strip()
        if key == "include":
            includes.append(value)
            continue
        directives[key] = value
    for pattern in includes:
        for path in sorted(glob.glob(pattern)):
            nested = read_text(path)
            if nested:
                directives.update(_parse_config_text(nested))
    return directives


def _load_file_directives() -> dict[str, str]:
    directives: dict[str, str] = {}
    for pattern in _CONFIG_PATHS:
        if "*" in pattern:
            paths = sorted(glob.glob(pattern))
        else:
            paths = [pattern]
        for path in paths:
            raw = read_text(path)
            if raw:
                directives.update(_parse_config_text(raw))
    return directives


def _effective_directives() -> tuple[dict[str, str], str | None]:
    """Prefer `sshd -T` (effective runtime config); fall back to config files. Read-only."""
    if shutil.which("sshd"):
        output = run(["sshd", "-T"], timeout=4.0)
        if output and "port" in output.lower():
            return _parse_sshd_t(output), "sshd -T"
    files = _load_file_directives()
    if files:
        return files, "sshd_config"
    return {}, None


def collect() -> dict | None:
    directives, source = _effective_directives()
    if not directives and source is None:
        return None

    port_raw = directives.get("port")
    port: int | None = None
    if port_raw:
        try:
            # sshd -T may list multiple ports; take the first.
            port = int(port_raw.split()[0])
        except (TypeError, ValueError, IndexError):
            port = None

    root_raw = directives.get("permitrootlogin")
    password_raw = directives.get("passwordauthentication")
    pubkey_raw = directives.get("pubkeyauthentication")
    protocol_raw = directives.get("protocol")

    result: dict[str, Any] = {
        "permit_root_login": _root_login_enabled(root_raw),
        "permit_root_login_raw": root_raw,
        "password_authentication": _truthy(password_raw),
        "password_authentication_raw": password_raw,
        "pubkey_authentication": _truthy(pubkey_raw),
        "pubkey_authentication_raw": pubkey_raw,
        "port": port,
        "protocol": protocol_raw,
        "config_source": source,
    }
    return result
