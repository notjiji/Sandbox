import type { AssetCriticality, AssetEnvironment, AssetStatus } from "@/shared/types/asset";

export const UNAVAILABLE = "Not available";

export const AUDIT_ACTION_LABELS: Record<string, string> = {
  "asset.create": "Created",
  "asset.update": "Updated",
  "asset.delete": "Deleted",
  "asset.archive": "Archived",
  "asset.restore": "Restored",
};

export function formatAuditAction(action: string): string {
  return AUDIT_ACTION_LABELS[action] ?? action.replace("asset.", "").replaceAll("_", " ");
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return UNAVAILABLE;
  return new Date(value).toLocaleString();
}

export function formatActor(actor: { name?: string | null; email?: string | null } | null | undefined): string {
  if (!actor) return "—";
  if (actor.name?.trim()) return actor.name.trim();
  if (actor.email?.trim()) return actor.email.trim();
  return "—";
}

export function formatRiskScore(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return UNAVAILABLE;
  return score.toFixed(1);
}

export function formatCount(value: number | null | undefined): string {
  if (value == null) return "0";
  return String(value);
}

export function criticalityClass(criticality: AssetCriticality | string): string {
  switch (criticality) {
    case "critical":
      return "border-red-500/40 bg-red-950/40 text-red-300";
    case "high":
      return "border-orange-500/40 bg-orange-950/40 text-orange-300";
    case "medium":
      return "border-yellow-500/40 bg-yellow-950/40 text-yellow-200";
    case "low":
      return "border-brand-600/40 bg-brand-950/40 text-brand-300";
    default:
      return "border-brand-700/40 bg-brand-900/40 text-brand-300";
  }
}

export function statusClass(status: AssetStatus | string): string {
  switch (status) {
    case "active":
      return "border-emerald-500/40 bg-emerald-950/40 text-emerald-300";
    case "pending":
      return "border-sky-500/40 bg-sky-950/40 text-sky-300";
    case "archived":
      return "border-brand-600/40 bg-brand-900/40 text-brand-300";
    case "deleted":
      return "border-red-700/40 bg-red-950/30 text-red-400";
    default:
      return "border-brand-700/40 bg-brand-900/40 text-brand-300";
  }
}

export function environmentClass(environment: AssetEnvironment | string): string {
  switch (environment) {
    case "production":
      return "border-purple-500/40 bg-purple-950/40 text-purple-200";
    case "staging":
      return "border-indigo-500/40 bg-indigo-950/40 text-indigo-200";
    case "development":
      return "border-teal-500/40 bg-teal-950/40 text-teal-200";
    case "testing":
      return "border-cyan-500/40 bg-cyan-950/40 text-cyan-200";
    default:
      return "border-brand-700/40 bg-brand-900/40 text-brand-300";
  }
}
