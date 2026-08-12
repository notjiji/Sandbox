import type { DiskFilesystem } from "@/shared/types/monitoring";
import { cn } from "@/shared/lib/utils";
import { usageTone } from "../utils";

interface DiskUsagePanelProps {
  disks?: DiskFilesystem[];
}

const toneFill = {
  default: "bg-emerald-500/80",
  warning: "bg-amber-500/80",
  danger: "bg-orange-500/80",
  critical: "bg-rose-500/80",
};

function formatGb(value?: number | null): string {
  if (value == null) return "—";
  return `${value.toFixed(1)} GB`;
}

export default function DiskUsagePanel({ disks = [] }: DiskUsagePanelProps) {
  if (disks.length === 0) {
    return <p className="text-sm text-brand-600">Filesystem usage will appear after the first heartbeat.</p>;
  }

  return (
    <ul className="space-y-4">
      {disks.map((disk) => {
        const tone = usageTone(disk.usage_percent);
        const width = Math.max(0, Math.min(100, disk.usage_percent ?? 0));
        return (
          <li key={disk.filesystem}>
            <div className="mb-2 flex items-center justify-between gap-3">
              <span className="font-mono text-sm text-brand-100">{disk.filesystem}</span>
              <span className="text-sm tabular-nums text-brand-300">
                {disk.usage_percent != null ? `${disk.usage_percent.toFixed(0)}%` : "—"}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-void-100/80">
              <div
                className={cn("h-full rounded-full transition-all", toneFill[tone])}
                style={{ width: `${width}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-brand-500">
              {formatGb(disk.used_gb)} used · {formatGb(disk.available_gb)} free · {formatGb(disk.total_gb)} total
            </p>
          </li>
        );
      })}
    </ul>
  );
}
