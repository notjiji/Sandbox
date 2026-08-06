from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cloud.schemas import BucketPolicyStatement, CloudRawResponse


async def collect(asset: ScanTarget, options: ScanOptions) -> CloudRawResponse:
    return CloudRawResponse(
        resource_id=asset.identifier,
        policy_statements=[
            BucketPolicyStatement(effect="Allow", principal="*", action="s3:GetObject"),
        ],
    )
