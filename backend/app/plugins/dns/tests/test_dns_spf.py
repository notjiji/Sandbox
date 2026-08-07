from app.plugins.dns.spf import count_spf_dns_lookups


class _FakeAnswer:
    def __init__(self, records: list[str]) -> None:
        self._records = [
            type("TXT", (), {"strings": [record.encode("utf-8")]})() for record in records
        ]

    def __iter__(self):
        return iter(self._records)


class _FakeResolver:
    def __init__(self, mapping: dict[str, str | None]) -> None:
        self.mapping = mapping

    def resolve(self, domain: str, rdtype: str):
        if rdtype != "TXT":
            raise Exception("unexpected type")
        record = self.mapping.get(domain)
        if record is None:
            raise __import__("dns").resolver.NoAnswer()
        return _FakeAnswer([record])


def test_count_spf_dns_lookups_follows_include_chain() -> None:
    resolver = _FakeResolver(
        {
            "example.com": "v=spf1 include:spf.example.com -all",
            "spf.example.com": "v=spf1 include:mail.example.com -all",
            "mail.example.com": "v=spf1 a mx -all",
        }
    )
    count = count_spf_dns_lookups("example.com", "v=spf1 include:spf.example.com -all", resolver)
    assert count == 4
