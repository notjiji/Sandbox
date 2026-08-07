from app.shared.schemas.base import BaseSchema


class SecurityTxtRawResponse(BaseSchema):
    url: str
    body: str = ""
    status_code: int | None = None
    final_url: str | None = None
    error: str | None = None


class SecurityTxtFieldValidation(BaseSchema):
    field: str
    valid: bool
    message: str | None = None


class SecurityTxtParsedData(BaseSchema):
    url: str
    final_url: str | None = None
    status_code: int | None = None
    present: bool = False
    path: str = "/.well-known/security.txt"
    contacts: list[str] = []
    encryption: list[str] = []
    expires: str | None = None
    expires_at: str | None = None
    expires_valid: bool = False
    expires_expired: bool = False
    canonical: list[str] = []
    acknowledgments: list[str] = []
    policy: list[str] = []
    hiring: list[str] = []
    preferred_languages: list[str] = []
    has_required_contact: bool = False
    contact_valid: bool = False
    encryption_valid: bool = True
    canonical_valid: bool = True
    canonical_matches: bool | None = None
    validation_issues: list[str] = []
    field_validations: list[SecurityTxtFieldValidation] = []
    error: str | None = None
