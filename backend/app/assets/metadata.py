"""Asset metadata types and helpers — extensible key/value and enrichment data."""

from dataclasses import dataclass, field


@dataclass
class AssetMetadata:
    """Structured metadata attached to an asset (DNS, WHOIS, tags, etc.)."""

    asset_id: str
    source: str
    data: dict = field(default_factory=dict)

    def get(self, key: str, default=None):
        return self.data.get(key, default)
