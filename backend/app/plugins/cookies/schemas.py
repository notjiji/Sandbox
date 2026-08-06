from app.shared.schemas.base import BaseSchema


class CookieRaw(BaseSchema):
    name: str
    secure: bool
    httponly: bool


class CookiesRawResponse(BaseSchema):
    url: str
    set_cookie_headers: list[str]


class CookiesParsedData(BaseSchema):
    cookies: list[CookieRaw]
    session_cookies: list[CookieRaw]
