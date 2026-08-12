from __future__ import annotations

from agent.collectors._util import load_psutil

_SKIP_FSTYPES = frozenset(
    {
        "squashfs",
        "tmpfs",
        "devtmpfs",
        "overlay",
        "proc",
        "sysfs",
        "devfs",
        "autofs",
        "cgroup",
        "cgroup2",
    }
)


def _usage_percent(usage) -> float:
    if hasattr(usage, "percent") and usage.percent is not None:
        return float(usage.percent)
    if usage.total:
        return (usage.used / usage.total) * 100
    return 0.0


def collect() -> dict:
    psutil = load_psutil()
    if psutil is None:
        return {
            "disks": [],
            "disk_percent": None,
            "disk_used_gb": None,
            "disk_total_gb": None,
        }

    disks: list[dict] = []
    seen: set[str] = set()
    for part in psutil.disk_partitions(all=False):
        mount = part.mountpoint
        if not mount or mount in seen:
            continue
        fstype = (part.fstype or "").lower()
        if fstype in _SKIP_FSTYPES:
            continue
        try:
            usage = psutil.disk_usage(mount)
        except (OSError, PermissionError):
            continue
        seen.add(mount)
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        available_gb = usage.free / (1024**3)
        pct = round(_usage_percent(usage), 1)
        disks.append(
            {
                "filesystem": mount,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "available_gb": round(available_gb, 2),
                "usage_percent": pct,
            }
        )

    disks.sort(key=lambda item: item["filesystem"])
    root = next((item for item in disks if item["filesystem"] in {"/", "C:\\", "C:/"}), None)
    primary = root or (max(disks, key=lambda item: item["usage_percent"]) if disks else None)
    return {
        "disks": disks,
        "disk_percent": primary["usage_percent"] if primary else None,
        "disk_used_gb": primary["used_gb"] if primary else None,
        "disk_total_gb": primary["total_gb"] if primary else None,
    }
