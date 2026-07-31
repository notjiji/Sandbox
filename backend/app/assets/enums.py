import enum


class AssetType(str, enum.Enum):
    """Digital asset types owned by the Asset Service."""

    WEBSITE = "website"
    DOMAIN = "domain"
    PUBLIC_IP = "public_ip"
    SERVER = "server"
    WINDOWS_SERVER = "windows_server"
    DOCKER_HOST = "docker_host"
    CLOUD_ACCOUNT = "cloud_account"
    KUBERNETES_CLUSTER = "kubernetes_cluster"
    API_ENDPOINT = "api_endpoint"
    MOBILE_APPLICATION = "mobile_application"
    GIT_REPOSITORY = "git_repository"
    EMAIL_DOMAIN = "email_domain"
    S3_BUCKET = "s3_bucket"
    AZURE_SUBSCRIPTION = "azure_subscription"


# Child asset → required parent type.
CHILD_PARENT_MAP: dict[AssetType, AssetType] = {
    AssetType.PUBLIC_IP: AssetType.WEBSITE,
    AssetType.EMAIL_DOMAIN: AssetType.DOMAIN,
    AssetType.S3_BUCKET: AssetType.CLOUD_ACCOUNT,
}

CHILD_ASSET_TYPES: frozenset[AssetType] = frozenset(CHILD_PARENT_MAP.keys())

ROOT_ASSET_TYPES: frozenset[AssetType] = frozenset(
    asset_type for asset_type in AssetType if asset_type not in CHILD_ASSET_TYPES
)

# Parent types that may have child assets attached.
PARENT_ASSET_TYPES: frozenset[AssetType] = frozenset(CHILD_PARENT_MAP.values())


class AssetStatus(str, enum.Enum):
    """Asset lifecycle — only ACTIVE assets can be scanned."""

    PENDING = "pending"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AssetEnvironment(str, enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"


class AssetCriticality(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Multipliers for risk scoring based on asset business importance.
CRITICALITY_RISK_MULTIPLIERS: dict[AssetCriticality, float] = {
    AssetCriticality.CRITICAL: 4.0,
    AssetCriticality.HIGH: 2.0,
    AssetCriticality.MEDIUM: 1.0,
    AssetCriticality.LOW: 0.25,
}
