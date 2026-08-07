"""Deep Content-Security-Policy directive analysis."""

from __future__ import annotations

import re

_BROAD_SOURCE_TOKENS = ("data:", "blob:", "https:")


def _directives(csp: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for chunk in csp.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(None, 1)
        name = parts[0].lower()
        values = parts[1].split() if len(parts) == 2 else []
        parsed[name] = values
    return parsed


def analyze_csp_deep(csp: str | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if not csp:
        return False, False, False, False, False, False

    lower = csp.lower()
    unsafe_inline = "'unsafe-inline'" in lower or " unsafe-inline" in lower
    unsafe_eval = "'unsafe-eval'" in lower or " unsafe-eval" in lower
    wildcard = " *" in csp or csp.strip().startswith("*")

    directives = _directives(csp)
    sensitive = ("default-src", "script-src", "script-src-elem", "object-src", "base-uri")
    has_data = False
    has_blob = False
    has_broad_https = False

    for name in sensitive:
        values = directives.get(name, [])
        for value in values:
            token = value.lower().rstrip(";")
            if token == "data:":
                has_data = True
            if token == "blob:":
                has_blob = True
            if token == "https:":
                has_broad_https = True

    return unsafe_inline, unsafe_eval, wildcard, has_data, has_blob, has_broad_https
