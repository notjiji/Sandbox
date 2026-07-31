"""Asset metadata — type-specific key/value storage and scan resolution."""

from dataclasses import dataclass, field

from app.assets.enums import AssetType
from app.assets.models import Asset, AssetMetadataEntry

PRIMARY_METADATA_KEYS: dict[AssetType, str] = {
    AssetType.WEBSITE: "url",
    AssetType.DOMAIN: "domain",
    AssetType.PUBLIC_IP: "address",
    AssetType.SERVER: "hostname",
    AssetType.WINDOWS_SERVER: "hostname",
    AssetType.DOCKER_HOST: "hostname",
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


def metadata_to_dict(entries: list[AssetMetadataEntry]) -> dict[str, str]:
    return {entry.key: entry.value for entry in entries}


def resolve_primary_value(asset: Asset, metadata: dict[str, str]) -> str:
    """Return the primary scan identifier from metadata, falling back to name."""
    primary_key = PRIMARY_METADATA_KEYS.get(asset.type)
    if primary_key and metadata.get(primary_key):
        return metadata[primary_key]
    return asset.name


def build_asset_metadata(
    asset: Asset,
    *,
    metadata: dict[str, str],
    children: list[Asset] | None = None,
    child_metadata: dict[str, dict[str, str]] | None = None,
) -> dict:
    """Build a metadata payload for scan and enrichment consumers."""
    identifier = resolve_primary_value(asset, metadata)
    payload: dict = {
        "asset_type": asset.type.value,
        "identifier": identifier,
        "status": asset.status.value,
        "environment": asset.environment.value,
        "criticality": asset.criticality.value,
        "metadata": metadata,
    }

    primary_key = PRIMARY_METADATA_KEYS.get(asset.type)
    if primary_key and primary_key in metadata:
        payload[primary_key] = metadata[primary_key]

    if asset.parent_id:
        payload["parent_id"] = str(asset.parent_id)

    if asset.owner:
        payload["owner"] = asset.owner

    if children:
        child_metadata = child_metadata or {}
        payload["children"] = [
            {
                "asset_id": str(child.id),
                "type": child.type.value,
                "identifier": resolve_primary_value(child, child_metadata.get(str(child.id), {})),
            }
            for child in children
        ]

        if asset.type == AssetType.WEBSITE:
            payload["public_ips"] = [
                item for item in payload["children"] if item["type"] == AssetType.PUBLIC_IP.value
            ]
        if asset.type == AssetType.DOMAIN:
            payload["email_domains"] = [
                item
                for item in payload["children"]
                if item["type"] == AssetType.EMAIL_DOMAIN.value
            ]
        if asset.type == AssetType.CLOUD_ACCOUNT:
            payload["s3_buckets"] = [
                item for item in payload["children"] if item["type"] == AssetType.S3_BUCKET.value
            ]

    return payload
