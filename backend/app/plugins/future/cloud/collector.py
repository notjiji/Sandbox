"""Detect public S3 bucket exposure via anonymous HTTP requests."""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cloud.schemas import BucketPolicyStatement, CloudRawResponse

_BUCKET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


def _extract_bucket_name(identifier: str) -> str | None:
    cleaned = identifier.strip()
    if cleaned.startswith("s3://"):
        return cleaned[5:].split("/", 1)[0] or None
    if cleaned.startswith(("http://", "https://")):
        parsed = urlparse(cleaned)
        host = parsed.hostname or ""
        if ".s3." in host or host.endswith(".s3.amazonaws.com"):
            return host.split(".s3.", 1)[0]
        if host.startswith("s3.") and parsed.path:
            return parsed.path.strip("/").split("/", 1)[0] or None
    if _BUCKET_NAME_RE.match(cleaned):
        return cleaned
    return None


def _bucket_urls(bucket: str) -> list[str]:
    return [
        f"https://{bucket}.s3.amazonaws.com/",
        f"https://s3.amazonaws.com/{bucket}/",
    ]


async def collect(asset: ScanTarget, options: ScanOptions) -> CloudRawResponse:
    bucket = _extract_bucket_name(asset.identifier)
    if not bucket:
        return CloudRawResponse(resource_id=asset.identifier, policy_statements=[])

    timeout = httpx.Timeout(min(options.timeout, 15.0), connect=min(options.timeout, 8.0))
    statements: list[BucketPolicyStatement] = []

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for url in _bucket_urls(bucket):
            try:
                response = await client.get(url)
            except httpx.HTTPError:
                continue
            body = response.text[:4096]
            if response.status_code == 200 and "<ListBucketResult" in body:
                statements.append(
                    BucketPolicyStatement(effect="Allow", principal="*", action="s3:ListBucket")
                )
            if response.status_code in {200, 403} and "AccessDenied" not in body and "ListBucketResult" in body:
                statements.append(
                    BucketPolicyStatement(effect="Allow", principal="*", action="s3:GetObject")
                )

    return CloudRawResponse(resource_id=bucket, policy_statements=statements)
