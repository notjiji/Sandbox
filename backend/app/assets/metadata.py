"""Asset metadata — enrichment data keyed by asset type."""

from dataclasses import dataclass, field

from app.assets.enums import AssetType
from app.assets.models import Asset

_IDENTIFIER_KEYS: dict[AssetType, str] = {
    AssetType.WEBSITE: "url",
    AssetType.DOMAIN: "domain",
    AssetType.PUBLIC_IP: "address",
    AssetType.SERVER: "host",
    AssetType.WINDOWS_SERVER: "host",
    AssetType.DOCKER_HOST: "host",
    AssetType.CLOUD_ACCOUNT: "account_id",
    AssetType.KUBERNETES_CLUSTER: "cluster",
    AssetType.API_ENDPOINT: "endpoint",
    AssetType.MOBILE_APPLICATION: "bundle_id",
    AssetType.GIT_REPOSITORY: "repository",
    AssetType.EMAIL_DOMAIN: "email_domain",
    AssetType.S3_BUCKET: "bucket",
    AssetType.AZURE_SUBSCRIPTION: "subscription_id",
}


@dataclass
class AssetMetadata:
    """Structured metadata attached to an asset (DNS, WHOIS, tags, etc.)."""

    asset_id: str
    source: str
    data: dict = field(default_factory=dict)

    def get(self, key: str, default=None):
        return self.data.get(key, default)


def build_asset_metadata(asset: Asset, *, children: list[Asset] | None = None) -> dict:
    """Build a metadata payload for scan and enrichment consumers."""
    identifier = asset.identifier or asset.name
    metadata: dict = {
        "asset_type": asset.type.value,
        "identifier": identifier,
        "status": asset.status.value,
    }

    key = _IDENTIFIER_KEYS.get(asset.type)
    if key:
        metadata[key] = identifier

    if asset.parent_id:
        metadata["parent_id"] = str(asset.parent_id)

    if children:
        metadata["children"] = [
            {
                "asset_id": str(child.id),
                "type": child.type.value,
                "identifier": child.identifier or child.name,
            }
            for child in children
        ]

        if asset.type == AssetType.WEBSITE:
            metadata["public_ips"] = [
                item for item in metadata["children"] if item["type"] == AssetType.PUBLIC_IP.value
            ]
        if asset.type == AssetType.DOMAIN:
            metadata["email_domains"] = [
                item for item in metadata["children"] if item["type"] == AssetType.EMAIL_DOMAIN.value
            ]
        if asset.type == AssetType.CLOUD_ACCOUNT:
            metadata["s3_buckets"] = [
                item for item in metadata["children"] if item["type"] == AssetType.S3_BUCKET.value
            ]

    return metadata
