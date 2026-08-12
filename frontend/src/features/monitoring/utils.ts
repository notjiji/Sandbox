import type { AgentStatus, AlertSeverity } from "@/shared/types/monitoring";

export const MONITORABLE_ASSET_TYPES = new Set(["server", "windows_server", "docker_host"]);

export function formatUptime(seconds?: number | null): string {
  if (seconds == null || seconds < 0) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function formatPercent(value?: number | null): string {
  if (value == null) return "—";
  return `${value.toFixed(0)}%`;
}

export function usageTone(value?: number | null): "default" | "warning" | "danger" {
  if (value == null) return "default";
  if (value >= 90) return "danger";
  if (value >= 75) return "warning";
  return "default";
}

export function agentStatusLabel(status: AgentStatus): string {
  switch (status) {
    case "online":
      return "Online";
    case "offline":
      return "Offline";
    case "pending":
      return "Waiting for heartbeat";
    case "revoked":
      return "Revoked";
    default:
      return status;
  }
}

export function severityClass(severity: AlertSeverity): string {
  switch (severity) {
    case "critical":
      return "border-rose-500/40 bg-rose-950/30 text-rose-200";
    case "high":
      return "border-orange-500/40 bg-orange-950/20 text-orange-200";
    case "medium":
      return "border-amber-500/40 bg-amber-950/20 text-amber-200";
    case "low":
      return "border-sky-500/40 bg-sky-950/20 text-sky-200";
    default:
      return "border-brand-700/40 bg-brand-950/20 text-brand-300";
  }
}

export function checkLabel(value?: boolean | null, yes = "Yes", no = "No"): string {
  if (value == null) return "Unknown";
  return value ? yes : no;
}
