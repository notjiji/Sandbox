from app.shared.schemas.base import BaseSchema


class RobotsRawResponse(BaseSchema):
    url: str
    body: str = ""
    status_code: int | None = None
    error: str | None = None


class RobotsPathRule(BaseSchema):
    path: str
    directive: str
    user_agent: str


class MatchedSensitivePath(BaseSchema):
    path: str
    category: str
    directive: str
    user_agent: str
    matched_pattern: str


class RobotsParsedData(BaseSchema):
    url: str
    status_code: int | None = None
    present: bool = False
    path: str = "/robots.txt"
    disallowed_paths: list[RobotsPathRule] = []
    allowed_paths: list[RobotsPathRule] = []
    sitemaps: list[str] = []
    user_agents: list[str] = []
    matched_paths: list[MatchedSensitivePath] = []
    admin_paths: list[str] = []
    debug_paths: list[str] = []
    sensitive_paths: list[str] = []
    rule_count: int = 0
    error: str | None = None
