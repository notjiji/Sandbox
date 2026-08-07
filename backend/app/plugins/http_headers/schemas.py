from app.shared.schemas.base import BaseSchema


class HttpRedirect(BaseSchema):
    url: str
    status_code: int


class HttpCookieRaw(BaseSchema):
    name: str
    value: str
    domain: str | None = None
    path: str | None = None
    secure: bool = False
    httponly: bool = False
    samesite: str | None = None
    expires: str | None = None
    max_age: int | None = None
    raw: str | None = None


class HttpTiming(BaseSchema):
    total_ms: float
    elapsed_ms: float | None = None


class HttpProbeRaw(BaseSchema):
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    cookies: list[HttpCookieRaw]
    redirects: list[HttpRedirect]
    body: str
    body_length: int
    content_type: str | None = None
    timing: HttpTiming


class HttpTraceProbeRaw(BaseSchema):
    url: str
    status_code: int | None = None
    allowed: bool = False
    response_preview: str | None = None


class HttpHeadersRawResponse(BaseSchema):
    """Raw HTTP probe data — no findings."""

    primary: HttpProbeRaw
    http_probe: HttpProbeRaw | None = None
    trace_probe: HttpTraceProbeRaw | None = None


class ParsedCookie(BaseSchema):
    name: str
    secure: bool
    httponly: bool
    samesite: str | None = None
    is_session_like: bool = False


class SecurityHeaders(BaseSchema):
    content_security_policy: str | None = None
    strict_transport_security: str | None = None
    referrer_policy: str | None = None
    x_frame_options: str | None = None
    x_content_type_options: str | None = None
    permissions_policy: str | None = None


class HttpHeadersParsedData(BaseSchema):
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    server: str | None = None
    powered_by: str | None = None
    content_type: str | None = None
    cookies: list[ParsedCookie]
    redirects: list[HttpRedirect]
    security_headers: SecurityHeaders
    timing: HttpTiming
    body_length: int
    is_https: bool
    http_redirects_to_https: bool | None = None
    trace_enabled: bool = False
    weak_cookies: list[ParsedCookie]
    # Extended analysis
    csp_has_unsafe_inline: bool = False
    csp_has_unsafe_eval: bool = False
    csp_has_wildcard: bool = False
    csp_has_data_uri: bool = False
    csp_has_blob_uri: bool = False
    csp_has_broad_https: bool = False
    hsts_max_age: int | None = None
    hsts_includes_subdomains: bool = False
    hsts_preload: bool = False
    hsts_is_weak: bool = False
    mixed_content_urls: list[str] = []
    redirect_chain_issues: list[str] = []
    open_redirect_candidate: bool = False

    @property
    def has_x_content_type_options(self) -> bool:
        return bool(self.security_headers.x_content_type_options)

    @property
    def has_permissions_policy(self) -> bool:
        return bool(self.security_headers.permissions_policy)

    @property
    def has_csp(self) -> bool:
        return bool(self.security_headers.content_security_policy)

    @property
    def has_hsts(self) -> bool:
        return bool(self.security_headers.strict_transport_security)

    @property
    def has_referrer_policy(self) -> bool:
        return bool(self.security_headers.referrer_policy)

    @property
    def has_x_frame_options(self) -> bool:
        return bool(self.security_headers.x_frame_options)

    @property
    def server_exposed(self) -> bool:
        return bool(self.server or self.powered_by)
