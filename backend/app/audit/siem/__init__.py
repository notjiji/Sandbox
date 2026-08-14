"""SIEM export adapters. Failures never raise to the caller."""

from __future__ import annotations

import hashlib
import hmac
import json
import socket
from base64 import b64decode, b64encode
from datetime import UTC, datetime
from email.utils import formatdate
from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("sandbox.audit.siem")


class SiemSink(Protocol):
    def send(self, event: dict[str, Any]) -> None: ...


def build_siem_payload(record) -> dict[str, Any]:
    return {
        "source": "sandbox",
        "id": str(record.id),
        "timestamp": record.created_at.isoformat() if record.created_at else None,
        "action": record.action,
        "severity": record.severity,
        "organization_id": str(record.organization_id) if record.organization_id else None,
        "user_id": str(record.user_id) if record.user_id else None,
        "entity_type": record.resource_type,
        "entity_id": str(record.resource_id) if record.resource_id else None,
        "details": record.details or {},
        "ip_address": record.ip_address,
        "entry_hash": record.entry_hash,
        "prev_hash": record.prev_hash,
    }


class SyslogSink:
    def __init__(self, host: str, port: int, protocol: str = "udp") -> None:
        self.host = host
        self.port = port
        self.protocol = protocol.lower()

    def send(self, event: dict[str, Any]) -> None:
        pri = 14  # user.notice
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = json.dumps(event, default=str)
        message = f"<{pri}>1 {timestamp} sandbox sandbox-audit - - - {body}\n"
        encoded = message.encode("utf-8")
        if self.protocol == "tcp":
            with socket.create_connection((self.host, self.port), timeout=2) as sock:
                sock.sendall(encoded)
            return
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2)
            sock.sendto(encoded, (self.host, self.port))


class SplunkHecSink:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token

    def send(self, event: dict[str, Any]) -> None:
        endpoint = self.url
        if not endpoint.endswith("/event"):
            endpoint = f"{endpoint}/services/collector/event"
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                endpoint,
                headers={
                    "Authorization": f"Splunk {self.token}",
                    "Content-Type": "application/json",
                },
                json={"event": event, "sourcetype": "sandbox:audit", "source": "sandbox"},
            )
            response.raise_for_status()


class ElkSink:
    def __init__(self, url: str, index: str, api_key: str = "") -> None:
        self.url = url.rstrip("/")
        self.index = index
        self.api_key = api_key

    def send(self, event: dict[str, Any]) -> None:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                f"{self.url}/{self.index}/_doc",
                headers=headers,
                json=event,
            )
            response.raise_for_status()


class SentinelSink:
    def __init__(self, workspace_id: str, shared_key: str, log_type: str) -> None:
        self.workspace_id = workspace_id
        self.shared_key = shared_key
        self.log_type = log_type

    def send(self, event: dict[str, Any]) -> None:
        body = json.dumps([event], default=str)
        rfc1123 = formatdate(usegmt=True)
        content_length = len(body.encode("utf-8"))
        string_to_hash = f"POST\n{content_length}\napplication/json\nx-ms-date:{rfc1123}\n/api/logs"
        decoded_key = b64decode(self.shared_key)
        signature = b64encode(
            hmac.new(decoded_key, string_to_hash.encode("utf-8"), hashlib.sha256).digest()
        ).decode("ascii")
        uri = (
            f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs"
            "?api-version=2016-04-01"
        )
        with httpx.Client(timeout=2.0) as client:
            response = client.post(
                uri,
                headers={
                    "Content-Type": "application/json",
                    "Log-Type": self.log_type,
                    "x-ms-date": rfc1123,
                    "Authorization": f"SharedKey {self.workspace_id}:{signature}",
                },
                content=body,
            )
            response.raise_for_status()


def get_siem_sink() -> SiemSink | None:
    settings = get_settings()
    sink = (settings.AUDIT_SIEM_SINK or "none").strip().lower()
    if sink in {"", "none", "off"}:
        return None
    if sink == "syslog":
        if not settings.AUDIT_SYSLOG_HOST:
            return None
        return SyslogSink(
            settings.AUDIT_SYSLOG_HOST,
            settings.AUDIT_SYSLOG_PORT,
            settings.AUDIT_SYSLOG_PROTOCOL,
        )
    if sink == "splunk":
        if not settings.AUDIT_SPLUNK_HEC_URL or not settings.AUDIT_SPLUNK_HEC_TOKEN:
            return None
        return SplunkHecSink(settings.AUDIT_SPLUNK_HEC_URL, settings.AUDIT_SPLUNK_HEC_TOKEN)
    if sink == "elk":
        if not settings.AUDIT_ELK_URL:
            return None
        return ElkSink(settings.AUDIT_ELK_URL, settings.AUDIT_ELK_INDEX, settings.AUDIT_ELK_API_KEY)
    if sink == "sentinel":
        if not settings.AUDIT_SENTINEL_WORKSPACE_ID or not settings.AUDIT_SENTINEL_SHARED_KEY:
            return None
        return SentinelSink(
            settings.AUDIT_SENTINEL_WORKSPACE_ID,
            settings.AUDIT_SENTINEL_SHARED_KEY,
            settings.AUDIT_SENTINEL_LOG_TYPE,
        )
    logger.warning("unknown SIEM sink", extra={"sink": sink})
    return None
