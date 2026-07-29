from app.schemas.base import BaseSchema


class UserProfileResponse(BaseSchema):
    id: str
    first_name: str
    last_name: str
    email: str
    role: str | None = None
    organization: str | None = None
