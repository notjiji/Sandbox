from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any


class AgentApi:
    def __init__(self, *, api_url: str, timeout_seconds: float) -> None:
        self._api_url = api_url.rstrip("/")
        self._timeout = timeout_seconds

    def register(self, *, enrollment_token: str, hostname: str, agent_version: str) -> dict[str, Any]:
        return self._post(
            "/monitoring/register",
            {
                "enrollment_token": enrollment_token,
                "hostname": hostname,
                "agent_version": agent_version,
            },
        )

    def ingest(self, *, credential: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/monitoring/ingest", payload, credential=credential)

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        credential: str | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "sandbox-agent/1.0",
        }
        if credential:
            headers["Authorization"] = f"Bearer {credential}"
        request = urllib.request.Request(
            f"{self._api_url}{path}",
            data=body,
            method="POST",
            headers=headers,
        )
        context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(request, timeout=self._timeout, context=context) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{path} failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"{path} unreachable: {exc.reason}") from exc

        parsed = json.loads(raw) if raw else {}
        if isinstance(parsed, dict) and "data" in parsed:
            data = parsed["data"]
            return data if isinstance(data, dict) else {}
        return parsed if isinstance(parsed, dict) else {}
