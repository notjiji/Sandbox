from app.plugins.ssl.ct import analyze_ct_issuers, is_trusted_ca_issuer


def test_is_trusted_ca_issuer() -> None:
    assert is_trusted_ca_issuer("C=US, O=Let's Encrypt, CN=R3") is True
    assert is_trusted_ca_issuer("C=XX, O=Totally Fake CA, CN=Root") is False


def test_analyze_ct_issuers_flags_unknown_ca(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.plugins.ssl.ct.fetch_crtsh_entries",
        lambda domain: [
            {"issuer_name": "C=US, O=Let's Encrypt, CN=R3"},
            {"issuer_name": "C=XX, O=Evil CA, CN=Root"},
        ],
    )
    issuers, suspicious = analyze_ct_issuers("example.com", "C=US, O=Let's Encrypt, CN=R3")
    assert len(issuers) == 2
    assert any("evil ca" in item for item in suspicious)
