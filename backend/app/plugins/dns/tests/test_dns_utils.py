from app.plugins.dns.utils import extract_domain, is_weak_spf


def test_extract_domain() -> None:
    assert extract_domain("https://Example.com/path") == "example.com"
    assert extract_domain("mail.example.com:25") == "mail.example.com"


def test_is_weak_spf() -> None:
    assert is_weak_spf("v=spf1 +all") is True
    assert is_weak_spf("v=spf1 include:_spf.example.com -all") is False
