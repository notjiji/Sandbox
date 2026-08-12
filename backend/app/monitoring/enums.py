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

AGENT_TOKEN_PREFIX = "sba_"
AGENT_OFFLINE_SECONDS = 600
DEFAULT_HISTORY_HOURS = 24
MAX_HISTORY_HOURS = 168
MAX_SNAPSHOTS = 500
