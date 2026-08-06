from app.plugins.dns.schemas import DnsParsedData, DnsRawResponse


def parse(raw: DnsRawResponse) -> DnsParsedData:
    txt_records = raw.records.get("TXT", [])
    return DnsParsedData(
        domain=raw.domain,
        a_records=raw.records.get("A", []),
        txt_records=txt_records,
        has_spf=any("v=spf1" in txt for txt in txt_records),
    )
