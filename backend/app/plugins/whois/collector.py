"""Collect raw WHOIS records — no findings."""

from __future__ import annotations

import asyncio

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.schemas import WhoisRawResponse
from app.plugins.whois.utils import extract_domain, extract_emails, normalize_datetime, normalize_name_servers


def _collect_sync(domain: str) -> WhoisRawResponse:
    try:
        import whois
    except ImportError as exc:
        return WhoisRawResponse(domain=domain, query_error=f"python-whois not installed: {exc}")

    try:
        record = whois.whois(domain)
    except Exception as exc:
        return WhoisRawResponse(domain=domain, query_error=str(exc))

    if record is None:
        return WhoisRawResponse(domain=domain, query_error="Empty WHOIS response")

    registrar = record.get("registrar") if hasattr(record, "get") else getattr(record, "registrar", None)
    if isinstance(registrar, list):
        registrar = registrar[0] if registrar else None
    registrar = str(registrar).strip() if registrar else None

    registrant = record.get("org") or record.get("name") if hasattr(record, "get") else None
    if isinstance(registrant, list):
        registrant = registrant[0] if registrant else None
    registrant = str(registrant).strip() if registrant else None

    raw_emails = record.get("emails") if hasattr(record, "get") else getattr(record, "emails", None)
    if isinstance(raw_emails, str):
        raw_emails = [raw_emails]
    emails = extract_emails(registrant, *(raw_emails or []))

    raw_text = record.get("text") if hasattr(record, "get") else getattr(record, "text", None)
    if isinstance(raw_text, list):
        raw_text = "\n".join(str(item) for item in raw_text)
    elif raw_text is not None:
        raw_text = str(raw_text)

    return WhoisRawResponse(
        domain=domain,
        registrar=registrar,
        created=normalize_datetime(record.get("creation_date") if hasattr(record, "get") else getattr(record, "creation_date", None)),
        updated=normalize_datetime(record.get("updated_date") if hasattr(record, "get") else getattr(record, "updated_date", None)),
        expires=normalize_datetime(record.get("expiration_date") if hasattr(record, "get") else getattr(record, "expiration_date", None)),
        name_servers=normalize_name_servers(record.get("name_servers") if hasattr(record, "get") else getattr(record, "name_servers", None)),
        registrant=registrant,
        emails=emails,
        raw_text=raw_text,
    )


async def collect(asset: ScanTarget, options: ScanOptions) -> WhoisRawResponse:
    domain = extract_domain(asset.identifier)
    return await asyncio.to_thread(_collect_sync, domain)
