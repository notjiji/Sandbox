from app.shared.schemas.base import BaseSchema


class RobotsRawResponse(BaseSchema):
    url: str
    body: str
    status_code: int


class RobotsParsedData(BaseSchema):
    path: str
    rule_count: int
    disallowed_paths: list[str]
    admin_disallowed: bool
