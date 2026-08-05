import enum


class ScanType(str, enum.Enum):
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PluginRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SchedulePreset(str, enum.Enum):
    QUICK_DAILY = "quick_daily"
    FULL_SUNDAY = "full_sunday"
    SSL_12H = "ssl_12h"
    DNS_WEEKLY = "dns_weekly"
