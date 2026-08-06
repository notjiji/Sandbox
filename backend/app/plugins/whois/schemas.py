from app.shared.schemas.base import BaseSchema


class WhoisRawResponse(BaseSchema):
    domain: str
    expires: str
    days_until_expiry: int


class WhoisParsedData(BaseSchema):
    domain: str
    expires: str
    days_until_expiry: int
    expiring_soon: bool
