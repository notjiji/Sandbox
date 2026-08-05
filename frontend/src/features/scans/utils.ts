import type { ScanStatus, ScanSummary, ScanType } from "@/shared/types/scan";

export function profileLabel(scanType: ScanType | string): string {
  switch (scanType) {
    case "quick":
      return "Quick Scan";
    case "full":
      return "Full Scan";
    case "custom":
      return "Custom Scan";
    default:
      return `${scanType} scan`;
  }
}

export function statusClass(status: ScanStatus | string): string {
  switch (status) {
    case "completed":
      return "text-emerald-300";
    case "running":
      return "text-yellow-400";
    case "queued":
      return "text-blue-400";
    case "failed":
      return "text-red-400";
    case "cancelled":
      return "text-brand-500";
    default:
      return "text-brand-400";
  }
}

export function formatDuration(seconds?: number | null): string {
  if (seconds == null || Number.isNaN(seconds)) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return remainder > 0 ? `${minutes}m ${remainder}s` : `${minutes}m`;
}

export function scanDisplayDate(scan: ScanSummary): string {
  const lifecycle = scan.lifecycle;
  const iso =
    lifecycle?.completed_at ??
    lifecycle?.failed_at ??
    lifecycle?.cancelled_at ??
    lifecycle?.running_at ??
    scan.created_at;
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatScore(score?: number | null): string {
  if (score == null) return "—";
  return score.toFixed(1);
}
