from app.plugins.future.cloud.schemas import CloudParsedData, CloudRawResponse


def parse(raw: CloudRawResponse) -> CloudParsedData:
    public_read = any(
        stmt.effect.lower() == "allow"
        and stmt.principal in ("*", "anonymous")
        and "get" in stmt.action.lower()
        for stmt in raw.policy_statements
    )
    return CloudParsedData(resource_id=raw.resource_id, public_read_allowed=public_read)
