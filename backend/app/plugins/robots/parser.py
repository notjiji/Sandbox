from app.plugins.robots.schemas import RobotsParsedData, RobotsRawResponse


def parse(raw: RobotsRawResponse) -> RobotsParsedData:
    disallowed: list[str] = []
    for line in raw.body.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("disallow:"):
            path = stripped.split(":", 1)[1].strip()
            if path:
                disallowed.append(path)

    return RobotsParsedData(
        path="/robots.txt",
        rule_count=len(disallowed),
        disallowed_paths=disallowed,
        admin_disallowed=any("/admin" in path for path in disallowed),
    )
