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


# Types that may never be assigned a parent.
PURE_ROOT_TYPES: frozenset[AssetType] = frozenset(
    {
        AssetType.DOMAIN,
        AssetType.CLOUD_ACCOUNT,
        AssetType.AZURE_SUBSCRIPTION,
        AssetType.GIT_REPOSITORY,
        AssetType.MOBILE_APPLICATION,
    }
)

# Child type → allowed parent types (supports multi-level infrastructure chains).
ALLOWED_PARENT_TYPES: dict[AssetType, frozenset[AssetType]] = {
    AssetType.PUBLIC_IP: frozenset({AssetType.WEBSITE, AssetType.DOMAIN}),
    AssetType.EMAIL_DOMAIN: frozenset({AssetType.DOMAIN}),
    AssetType.S3_BUCKET: frozenset({AssetType.CLOUD_ACCOUNT}),
    AssetType.SERVER: frozenset({AssetType.PUBLIC_IP}),
    AssetType.WINDOWS_SERVER: frozenset({AssetType.PUBLIC_IP}),
    AssetType.DOCKER_HOST: frozenset({AssetType.SERVER, AssetType.WINDOWS_SERVER}),
    AssetType.WEBSITE: frozenset({AssetType.DOCKER_HOST, AssetType.SERVER, AssetType.DOMAIN}),
    AssetType.API_ENDPOINT: frozenset({AssetType.WEBSITE, AssetType.KUBERNETES_CLUSTER}),
    AssetType.KUBERNETES_CLUSTER: frozenset(
        {AssetType.CLOUD_ACCOUNT, AssetType.AZURE_SUBSCRIPTION}
    ),
}

REQUIRED_PARENT_TYPES: frozenset[AssetType] = frozenset(
    {
        AssetType.PUBLIC_IP,
        AssetType.EMAIL_DOMAIN,
        AssetType.S3_BUCKET,
        AssetType.SERVER,
        AssetType.WINDOWS_SERVER,
        AssetType.DOCKER_HOST,
    }
)

OPTIONAL_PARENT_TYPES: frozenset[AssetType] = frozenset(
    {
        AssetType.WEBSITE,
        AssetType.API_ENDPOINT,
        AssetType.KUBERNETES_CLUSTER,
    }
)

CHILD_ASSET_TYPES: frozenset[AssetType] = frozenset(ALLOWED_PARENT_TYPES.keys())

ROOT_ASSET_TYPES: frozenset[AssetType] = frozenset(
    asset_type for asset_type in AssetType if asset_type not in REQUIRED_PARENT_TYPES
)

PARENT_ASSET_TYPES: frozenset[AssetType] = frozenset(
    parent_type
    for parent_types in ALLOWED_PARENT_TYPES.values()
    for parent_type in parent_types
)

# Backward-compatible single-parent map (first allowed parent per child type).
CHILD_PARENT_MAP: dict[AssetType, AssetType] = {
    child: next(iter(parents)) for child, parents in ALLOWED_PARENT_TYPES.items()
}


class AssetLinkType(str, enum.Enum):
    DEPENDS_ON = "depends_on"
    HOSTS = "hosts"
    RUNS_ON = "runs_on"
    EXPOSES = "exposes"
    RELATED = "related"


class AssetStatus(str, enum.Enum):
    """Asset lifecycle — only ACTIVE assets can be scanned."""

    PENDING = "pending"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AssetHealthStatus(str, enum.Enum):
    """Security posture label for asset cards and dashboards."""

    HEALTHY = "Healthy"
    AT_RISK = "At Risk"
    CRITICAL = "Critical"
    UNSCANNED = "Unscanned"
    INACTIVE = "Inactive"


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


class AssetCategory(str, enum.Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    DATA = "data"
    NETWORK = "network"
    IDENTITY = "identity"
    ENDPOINT = "endpoint"
    CLOUD = "cloud"
    OTHER = "other"


class AssetSortField(str, enum.Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    CRITICALITY = "criticality"
    ENVIRONMENT = "environment"
    TYPE = "type"


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class AssetVerificationMethod(str, enum.Enum):
    DOMAIN = "domain"
    DNS_TXT = "dns_txt"
    HTTP = "http"
    IP_OWNERSHIP = "ip_ownership"


class AssetVerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


REQUIRED_SCAN_VERIFICATION_TYPES: frozenset[AssetType] = frozenset(
    {
        AssetType.WEBSITE,
        AssetType.DOMAIN,
        AssetType.PUBLIC_IP,
    }
)


DEFAULT_ASSET_CATEGORY_BY_TYPE: dict[AssetType, AssetCategory] = {
    AssetType.WEBSITE: AssetCategory.APPLICATION,
    AssetType.API_ENDPOINT: AssetCategory.APPLICATION,
    AssetType.MOBILE_APPLICATION: AssetCategory.APPLICATION,
    AssetType.GIT_REPOSITORY: AssetCategory.APPLICATION,
    AssetType.DOMAIN: AssetCategory.NETWORK,
    AssetType.PUBLIC_IP: AssetCategory.NETWORK,
    AssetType.EMAIL_DOMAIN: AssetCategory.NETWORK,
    AssetType.SERVER: AssetCategory.INFRASTRUCTURE,
    AssetType.WINDOWS_SERVER: AssetCategory.INFRASTRUCTURE,
    AssetType.DOCKER_HOST: AssetCategory.INFRASTRUCTURE,
    AssetType.KUBERNETES_CLUSTER: AssetCategory.INFRASTRUCTURE,
    AssetType.CLOUD_ACCOUNT: AssetCategory.CLOUD,
    AssetType.AZURE_SUBSCRIPTION: AssetCategory.CLOUD,
    AssetType.S3_BUCKET: AssetCategory.CLOUD,
}


# Multipliers for risk scoring based on asset business importance.
CRITICALITY_RISK_MULTIPLIERS: dict[AssetCriticality, float] = {
    AssetCriticality.CRITICAL: 4.0,
    AssetCriticality.HIGH: 2.0,
    AssetCriticality.MEDIUM: 1.0,
    AssetCriticality.LOW: 0.25,
}
