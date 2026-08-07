"""Parse robots.txt directives and detect sensitive path disclosures."""

from app.plugins.robots import sensitive_paths
from app.plugins.robots.schemas import RobotsParsedData, RobotsPathRule, RobotsRawResponse


def _strip_comment(line: str) -> str:
    if "#" in line:
        return line.split("#", 1)[0].strip()
    return line.strip()


def _parse_body(body: str) -> tuple[list[RobotsPathRule], list[RobotsPathRule], list[str], list[str]]:
    current_user_agent = "*"
    disallowed: list[RobotsPathRule] = []
    allowed: list[RobotsPathRule] = []
    sitemaps: list[str] = []
    user_agents: list[str] = []

    for raw_line in body.splitlines():
        line = _strip_comment(raw_line)
        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        directive = key.strip().lower()
        cleaned_value = value.strip()
        if not cleaned_value and directive not in {"disallow", "allow"}:
            continue

        if directive == "user-agent":
            current_user_agent = cleaned_value
            if cleaned_value not in user_agents:
                user_agents.append(cleaned_value)
        elif directive == "disallow":
            disallowed.append(
                RobotsPathRule(path=cleaned_value or "/", directive="disallow", user_agent=current_user_agent)
            )
        elif directive == "allow":
            allowed.append(
                RobotsPathRule(path=cleaned_value, directive="allow", user_agent=current_user_agent)
            )
        elif directive == "sitemap" and cleaned_value not in sitemaps:
            sitemaps.append(cleaned_value)

    return disallowed, allowed, sitemaps, user_agents


def parse(raw: RobotsRawResponse) -> RobotsParsedData:
    if raw.error:
        return RobotsParsedData(
            url=raw.url,
            status_code=raw.status_code,
            present=False,
            error=raw.error,
        )

    present = raw.status_code == 200 and bool(raw.body.strip())
    if not present:
        return RobotsParsedData(
            url=raw.url,
            status_code=raw.status_code,
            present=False,
        )

    disallowed, allowed, sitemaps, user_agents = _parse_body(raw.body)
    all_rules = disallowed + allowed
    matched = sensitive_paths.scan_rules(all_rules)
    admin_paths, debug_paths, sensitive_only = sensitive_paths.unique_paths_by_category(matched)

    return RobotsParsedData(
        url=raw.url,
        status_code=raw.status_code,
        present=True,
        disallowed_paths=disallowed,
        allowed_paths=allowed,
        sitemaps=sitemaps,
        user_agents=user_agents,
        matched_paths=matched,
        admin_paths=admin_paths,
        debug_paths=debug_paths,
        sensitive_paths=sensitive_only,
        rule_count=len(disallowed) + len(allowed) + len(sitemaps),
    )
