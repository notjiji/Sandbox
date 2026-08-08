"""Per-scan shared state for deduplicated probes and cross-plugin hints."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CachedHttpRedirect:
    url: str
    status_code: int


@dataclass
class CachedHttpProbe:
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    body: str
    body_length: int
    cookies: list[dict[str, str]] = field(default_factory=list)
    set_cookie_headers: list[str] = field(default_factory=list)
    redirects: list[CachedHttpRedirect] = field(default_factory=list)
    content_type: str | None = None
    timing_total_ms: float = 0.0


@dataclass
class ScanExecutionContext:
    http_primary: dict[str, CachedHttpProbe] = field(default_factory=dict)
    http_locks: dict[str, asyncio.Lock] = field(default_factory=dict)
    service_hints: list[dict[str, Any]] = field(default_factory=list)
    transport_hints: dict[str, Any] = field(default_factory=dict)


class ScanContext:
    _current: ContextVar[ScanExecutionContext | None] = ContextVar("scan_execution_context", default=None)

    def begin(self) -> None:
        self._current.set(ScanExecutionContext())

    def end(self) -> None:
        self._current.set(None)

    def get(self) -> ScanExecutionContext | None:
        return self._current.get()

    def publish_services(self, services: list[dict[str, Any]]) -> None:
        ctx = self.get()
        if ctx is None:
            return
        for service in services:
            if service not in ctx.service_hints:
                ctx.service_hints.append(service)

    def service_hints(self) -> list[dict[str, Any]]:
        ctx = self.get()
        return list(ctx.service_hints) if ctx else []

    def lock_for(self, key: str) -> asyncio.Lock:
        ctx = self.get()
        if ctx is None:
            return asyncio.Lock()
        if key not in ctx.http_locks:
            ctx.http_locks[key] = asyncio.Lock()
        return ctx.http_locks[key]

    def get_http_primary(self, key: str) -> CachedHttpProbe | None:
        ctx = self.get()
        if ctx is None:
            return None
        return ctx.http_primary.get(key)

    def set_http_primary(self, key: str, probe: CachedHttpProbe) -> None:
        ctx = self.get()
        if ctx is None:
            return
        ctx.http_primary[key] = probe

    def publish_transport_hints(self, hints: dict[str, Any]) -> None:
        ctx = self.get()
        if ctx is None:
            return
        ctx.transport_hints.update(hints)

    def transport_hints(self) -> dict[str, Any]:
        ctx = self.get()
        return dict(ctx.transport_hints) if ctx else {}


scan_context = ScanContext()
