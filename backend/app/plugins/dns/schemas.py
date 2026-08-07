"""DNS scanner data models."""

from app.shared.schemas.base import BaseSchema


class ResolverSnapshot(BaseSchema):
    resolver: str
    records: dict[str, list[str]]


class SubdomainCnameProbe(BaseSchema):
    subdomain: str
    cname_target: str | None = None
    resolves: bool = False


class MxHostProbe(BaseSchema):
    host: str
    a_records: list[str] = []
    ptr_records: list[str] = []


class DnsRawResponse(BaseSchema):
    """Raw DNS query results — no findings."""

    domain: str
    records: dict[str, list[str]]
    ttls: dict[str, int | None] = {}
    spf_records: list[str] = []
    dnskey_records: list[str] = []
    ds_records: list[str] = []
    rrsig_records: list[str] = []
    caa_records: list[str] = []
    dkim_records: dict[str, list[str]] = {}
    dmarc_records: list[str] = []
    mta_sts_records: list[str] = []
    tls_rpt_records: list[str] = []
    bimi_records: list[str] = []
    subdomain_probes: list[SubdomainCnameProbe] = []
    mx_probes: list[MxHostProbe] = []
    wildcard_probe: str | None = None
    wildcard_resolves: bool = False
    zone_transfer_allowed: bool = False
    query_errors: dict[str, str] = {}
    resolver_snapshots: list[ResolverSnapshot] = []
    ct_subdomains: list[str] = []
    ct_dkim_selectors: list[str] = []
    http_takeover_confirmed: list[str] = []
    dnssec_validated: bool | None = None
    dnssec_validation_error: str | None = None
    spf_recursive_lookup_count: int | None = None


class DnsParsedData(BaseSchema):
    domain: str
    a_records: list[str] = []
    aaaa_records: list[str] = []
    mx_records: list[str] = []
    txt_records: list[str] = []
    ns_records: list[str] = []
    soa_record: str | None = None
    cname_records: list[str] = []
    spf_record: str | None = None
    spf_records: list[str] = []
    spf_is_weak: bool = False
    spf_has_duplicate: bool = False
    spf_lookup_count: int = 0
    spf_too_many_lookups: bool = False
    dmarc_record: str | None = None
    dmarc_policy: str | None = None
    dmarc_is_weak: bool = False
    dmarc_missing_rua: bool = False
    dkim_selectors_found: list[str] = []
    dnssec_enabled: bool = False
    dnssec_has_ds: bool = False
    dnssec_has_rrsig: bool = False
    dnssec_incomplete: bool = False
    dnssec_validated: bool | None = None
    dnssec_validation_failed: bool = False
    caa_records: list[str] = []
    caa_present: bool = False
    mta_sts_present: bool = False
    tls_rpt_present: bool = False
    bimi_present: bool = False
    wildcard_detected: bool = False
    minimum_ttl: int | None = None
    subdomain_takeover_risks: list[str] = []
    mx_misconfigured: list[str] = []
    zone_transfer_allowed: bool = False
    resolver_discrepancies: list[str] = []
    ct_subdomains: list[str] = []
    http_takeover_confirmed: list[str] = []

    @property
    def has_spf(self) -> bool:
        return self.spf_record is not None
