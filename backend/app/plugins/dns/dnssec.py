"""DNSSEC validation via validating resolvers (AD flag)."""

from __future__ import annotations

import dns.flags
import dns.message
import dns.query
import dns.rdatatype

_VALIDATING_RESOLVERS = ("8.8.8.8", "1.1.1.1", "9.9.9.9")


def validate_dnssec(domain: str, timeout: float = 5.0) -> tuple[bool | None, str | None]:
    """Return (validated, error). None means inconclusive (no DNSSEC signal)."""
    last_error: str | None = None
    for nameserver in _VALIDATING_RESOLVERS:
        try:
            request = dns.message.make_query(domain, dns.rdatatype.A, want_dnssec=True)
            response = dns.query.udp(request, nameserver, timeout=timeout)
            if response.rcode() != 0:
                last_error = f"rcode {response.rcode()}"
                continue
            if response.flags & dns.flags.AD:
                return True, None

            has_rrsig = any(
                rrset.rdtype == dns.rdatatype.RRSIG
                for rrset in (*response.answer, *response.authority, *response.additional)
            )
            if has_rrsig:
                return False, "RRSIG records present but AD flag not set by validating resolver"
        except Exception as exc:
            last_error = str(exc)
            continue

    return None, last_error
