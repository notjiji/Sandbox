from __future__ import annotations

import re
import shutil

from agent.collectors._util import run


def _normalize_policy(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    cleaned = cleaned.replace("(incoming)", "").replace("(outgoing)", "").replace("(routed)", "")
    cleaned = cleaned.strip(" ,")
    if not cleaned:
        return None
    mapping = {
        "deny": "DENY",
        "drop": "DENY",
        "reject": "DENY",
        "allow": "ALLOW",
        "accept": "ALLOW",
    }
    return mapping.get(cleaned, cleaned.upper())


def _from_ufw() -> dict | None:
    if not shutil.which("ufw"):
        return None
    output = run(["ufw", "status", "verbose"], timeout=4.0)
    if output is None:
        # Binary exists but status unavailable (permissions).
        return {"enabled": None, "backend": "ufw", "default_incoming": None, "default_outgoing": None}
    enabled = "Status: active" in output
    incoming = outgoing = None
    for line in output.splitlines():
        if "Default:" not in line:
            continue
        # Default: deny (incoming), allow (outgoing), disabled (routed)
        body = line.split("Default:", 1)[-1]
        parts = [part.strip() for part in body.split(",")]
        for part in parts:
            lower = part.lower()
            if "incoming" in lower:
                incoming = _normalize_policy(lower.replace("incoming", ""))
            elif "outgoing" in lower:
                outgoing = _normalize_policy(lower.replace("outgoing", ""))
        break
    return {
        "enabled": enabled,
        "backend": "ufw",
        "default_incoming": incoming,
        "default_outgoing": outgoing,
    }


def _from_firewalld() -> dict | None:
    if not shutil.which("firewall-cmd"):
        return None
    state = run(["firewall-cmd", "--state"], timeout=3.0)
    enabled = (state or "").strip().lower() == "running"
    incoming = outgoing = None
    if enabled:
        zone = run(["firewall-cmd", "--get-default-zone"], timeout=3.0)
        if zone:
            target = run(["firewall-cmd", f"--zone={zone.strip()}", "--get-target"], timeout=3.0)
            incoming = _normalize_policy(target)
        # firewalld has no single global outgoing default comparable to UFW; leave None when unknown.
    return {
        "enabled": enabled,
        "backend": "firewalld",
        "default_incoming": incoming,
        "default_outgoing": outgoing,
    }


def _nft_policy(chain_output: str | None, chain_name: str) -> str | None:
    if not chain_output:
        return None
    # Look for `type filter hook input ... policy drop;`
    pattern = rf"hook\s+{re.escape(chain_name)}\b[^;]*\bpolicy\s+(\w+)"
    match = re.search(pattern, chain_output, flags=re.IGNORECASE)
    if match:
        return _normalize_policy(match.group(1))
    return None


def _from_nftables() -> dict | None:
    if not shutil.which("nft"):
        return None
    # Presence alone is not enough — only report when a ruleset exists or service is active.
    rules = run(["nft", "list", "ruleset"], timeout=4.0)
    service = run(["systemctl", "is-active", "nftables"], timeout=2.0)
    service_active = (service or "").strip() == "active"
    if rules is None and not service_active:
        return None
    has_rules = bool(rules and rules.strip())
    enabled = service_active or has_rules
    incoming = _nft_policy(rules, "input")
    outgoing = _nft_policy(rules, "output")
    return {
        "enabled": enabled if has_rules or service_active else None,
        "backend": "nftables",
        "default_incoming": incoming,
        "default_outgoing": outgoing,
    }


def _iptables_policy(table_output: str | None, chain: str) -> str | None:
    if not table_output:
        return None
    for line in table_output.splitlines():
        # -P INPUT DROP
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "-P" and parts[1].upper() == chain.upper():
            return _normalize_policy(parts[2])
    return None


def _from_iptables() -> dict | None:
    if not shutil.which("iptables"):
        return None
    output = run(["iptables", "-S"], timeout=4.0)
    if output is None:
        # May lack privileges; still report the mechanism if the binary exists and something looks configured.
        return None
    incoming = _iptables_policy(output, "INPUT")
    outgoing = _iptables_policy(output, "OUTPUT")
    # Consider enabled when policies are non-ACCEPT or there are non-policy rules.
    rule_lines = [line for line in output.splitlines() if line.strip() and not line.startswith("-P")]
    policies = {incoming, outgoing}
    enabled = bool(rule_lines) or any(p and p != "ALLOW" for p in policies)
    return {
        "enabled": enabled,
        "backend": "iptables",
        "default_incoming": incoming,
        "default_outgoing": outgoing,
    }


def collect() -> dict | None:
    """Read-only firewall assessment. Never modifies rules."""
    for collector in (_from_ufw, _from_firewalld, _from_nftables, _from_iptables):
        result = collector()
        if result is not None:
            return result
    return None
