"""Normalized metric types. Add a constant here — do not add a new DB column."""

CPU_USAGE = "cpu_usage"
CPU_CORES = "cpu_cores"
MEMORY_USAGE = "memory_usage"
MEMORY_USED = "memory_used"
MEMORY_TOTAL = "memory_total"
MEMORY_AVAILABLE = "memory_available"
DISK_USAGE = "disk_usage"
DISK_USED = "disk_used"
DISK_TOTAL = "disk_total"
DISK_AVAILABLE = "disk_available"
LOAD_AVERAGE = "load_average"
UPTIME = "uptime"
PROCESS_COUNT = "process_count"

UNIT_PERCENT = "percent"
UNIT_SECONDS = "seconds"
UNIT_MB = "mb"
UNIT_GB = "gb"
UNIT_COUNT = "count"
UNIT_RATIO = "ratio"

HISTORY_METRIC_TYPES = (CPU_USAGE, MEMORY_USAGE, DISK_USAGE)

ROOT_FILESYSTEMS = frozenset({"/", "C:\\", "C:/"})
