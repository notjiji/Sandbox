import enum

from app.assets.enums import AssetType


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    ONLINE = "online"
    OFFLINE = "offline"
    REVOKED = "revoked"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"


MONITORABLE_ASSET_TYPES = frozenset(
    {AssetType.SERVER, AssetType.WINDOWS_SERVER, AssetType.DOCKER_HOST}
)

ENROLLMENT_TOKEN_PREFIX = "sbe_"
CREDENTIAL_PREFIX = "sba_"
AGENT_TOKEN_PREFIX = CREDENTIAL_PREFIX  # ingest credential
AGENT_OFFLINE_SECONDS = 600
ENROLLMENT_TOKEN_EXPIRE_MINUTES = 15
DEFAULT_HISTORY_HOURS = 24
MAX_HISTORY_HOURS = 168
MAX_SNAPSHOTS = 500
