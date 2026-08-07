from app.shared.schemas.base import BaseSchema


class FingerprintCookieRaw(BaseSchema):
    name: str
    value: str = ""


class FingerprintRawResponse(BaseSchema):
    """Raw HTTP probe data for technology fingerprinting."""

    url: str
    final_url: str
    status_code: int | None = None
    headers: dict[str, str] = {}
    cookies: list[FingerprintCookieRaw] = []
    body: str = ""
    body_length: int = 0
    script_srcs: list[str] = []
    error: str | None = None


class DetectedTechnology(BaseSchema):
    name: str
    category: str
    confidence: float
    evidence: str
    source: str


class FingerprintParsedData(BaseSchema):
    url: str
    final_url: str
    status_code: int | None = None
    headers: dict[str, str] = {}
    cookie_names: list[str] = []
    script_srcs: list[str] = []
    technologies: list[DetectedTechnology] = []
    error: str | None = None
