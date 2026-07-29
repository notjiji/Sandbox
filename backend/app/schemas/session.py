from datetime import datetime

from app.schemas.base import BaseSchema


class SessionSummary(BaseSchema):
    id: str
    created_at: datetime
    expires_at: datetime
    is_current: bool


class SessionListResponse(BaseSchema):
    items: list[SessionSummary]
    total: int


class RevokeSessionResponse(BaseSchema):
    message: str
    revoked_current_session: bool = False
