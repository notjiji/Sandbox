"""DNS scanner helpers."""

import re
import uuid

_SPF_PATTERN = re.compile(r"v=spf1", re.IGNORECASE)
_DMARC_PATTERN = re.compile(r"v=DMARC1", re.IGNORECASE)
_SPF_LOOKUP_MECHANISMS = re.compile(r"\b(include|redirect|a|mx|ptr|exists|exp):", re.IGNORECASE)

_COMMON_DKIM_SELECTORS = (
    "default",
    "google",
    "k1",
    "k2",
    "s1",
    "s2",
    "selector1",
    "selector2",
    "selector",
    "dkim",
    "mail",
    "smtp",
    "mandrill",
    "sendgrid",
    "amazonses",
    "protonmail",
    "mailgun",
    "postmark",
    "zoho",
    "mimecast",
    "cm",
    "email",
)

_COMMON_SUBDOMAINS = (
    "www",
    "dev",
    "staging",
    "stage",
    "api",
    "mail",
    "test",
    "admin",
    "cdn",
    "app",
    "beta",
    "demo",
)


def extract_domain(identifier: str) -> str:
    cleaned = identifier.strip().replace("https://", "").replace("http://", "")
    host = cleaned.split("/")[0].split(":")[0]
    return host.rstrip(".").lower()


def wildcard_probe_name(domain: str) -> str:
    token = uuid.uuid4().hex[:12]
    return f"_sandbox-probe-{token}.{domain}"


def find_spf_records(txt_records: list[str]) -> list[str]:
    return [record for record in txt_records if _SPF_PATTERN.search(record)]


def find_spf_record(txt_records: list[str]) -> str | None:
    records = find_spf_records(txt_records)
    return records[0] if records else None


def find_dmarc_record(dmarc_records: list[str]) -> str | None:
    for record in dmarc_records:
        if _DMARC_PATTERN.search(record):
            return record
    return None


def estimate_spf_lookup_count(spf_record: str) -> int:
    return len(_SPF_LOOKUP_MECHANISMS.findall(spf_record))


def is_weak_spf(spf_record: str) -> bool:
    normalized = " ".join(spf_record.lower().split())
    if "+all" in normalized.replace(" ", ""):
        return True
    if "?all" in normalized:
        return True
    if " ptr" in f" {normalized} " or normalized.endswith(" ptr"):
        return True
    if "v=spf1" in normalized and "all" not in normalized:
        return True
    return False


def parse_dmarc_policy(dmarc_record: str) -> tuple[str | None, bool, bool]:
    tags = {}
    for part in dmarc_record.split(";"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            tags[key.strip().lower()] = value.strip()
    policy = tags.get("p")
    is_weak = policy is not None and policy.lower() == "none"
    missing_rua = "rua" not in tags and "ruf" not in tags
    return policy, is_weak, missing_rua


def dkim_selector_names(dkim_records: dict[str, list[str]]) -> list[str]:
    return sorted(name for name, values in dkim_records.items() if values)


def is_dangling_cname_target(target: str) -> bool:
    from app.plugins.dns.takeover import is_dangling_cname_target as _check

    return _check(target)


def parse_mx_host(mx_record: str) -> str:
    parts = mx_record.split(None, 1)
    return parts[1].rstrip(".").lower() if len(parts) == 2 else mx_record.rstrip(".").lower()
