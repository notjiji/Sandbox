"""Render finding evidence from rule templates."""

from __future__ import annotations

import re
from typing import Any

_TEMPLATE_RE = re.compile(r"\{([^{}]+)\}")


def _resolve_key(context: dict[str, Any], key: str) -> str:
    value = context.get(key.strip())
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return str(value)
    return str(value)


def render_template(template: str, context: dict[str, Any]) -> str:
    def replacer(match: re.Match[str]) -> str:
        return _resolve_key(context, match.group(1))

    return _TEMPLATE_RE.sub(replacer, template)
