from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None
    user_agent: str | None


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def build_request_context(request: Request) -> RequestContext:
    return RequestContext(
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
