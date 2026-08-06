from app.plugins.cookies.schemas import CookieRaw, CookiesParsedData, CookiesRawResponse


def _parse_cookie_header(header: str) -> CookieRaw:
    parts = [part.strip() for part in header.split(";")]
    name_value = parts[0]
    name = name_value.split("=", 1)[0].strip()
    flags = {part.lower() for part in parts[1:]}
    return CookieRaw(name=name, secure="secure" in flags, httponly="httponly" in flags)


def parse(raw: CookiesRawResponse) -> CookiesParsedData:
    cookies = [_parse_cookie_header(header) for header in raw.set_cookie_headers]
    session_cookies = [cookie for cookie in cookies if "session" in cookie.name.lower()]
    return CookiesParsedData(cookies=cookies, session_cookies=session_cookies)
