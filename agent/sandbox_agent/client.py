from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any


class AgentClient:
    def __init__(self, *, api_url: str, token: str, timeout_seconds: float) -> None:
        self._ingest_url = f"{api_url.rstrip('/')}/monitoring/ingest"
        self._token = token
        self._timeout = timeout_seconds

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._ingest_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "sandbox-agent/1.0",
            },
        )
        context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(request, timeout=self._timeout, context=context) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ingest failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ingest unreachable: {exc.reason}") from exc

        parsed = json.loads(raw) if raw else {}
        if isinstance(parsed, dict) and "data" in parsed:
            data = parsed["data"]
            return data if isinstance(data, dict) else {}
        return parsed if isinstance(parsed, dict) else {}
