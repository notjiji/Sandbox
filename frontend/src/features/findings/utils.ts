import type { FindingSeverity, FindingStatus } from "@/shared/types/finding";

export function severityClass(severity: FindingSeverity | string): string {
  switch (severity) {
    case "critical":
      return "text-red-300";
    case "high":
      return "text-orange-300";
    case "medium":
      return "text-yellow-200";
    case "low":
      return "text-brand-300";
    default:
      return "text-brand-400";
  }
}

export function statusLabel(status: FindingStatus | string): string {
  switch (status) {
    case "open":
      return "Open";
    case "in_review":
      return "In review";
    case "resolved":
      return "Resolved";
    case "false_positive":
    case "accepted":
      return "Ignored";
    default:
      return status.replace(/_/g, " ");
  }
}

export function statusClass(status: FindingStatus | string): string {
  switch (status) {
    case "open":
      return "text-red-300";
    case "in_review":
      return "text-yellow-300";
    case "resolved":
      return "text-emerald-300";
    case "false_positive":
    case "accepted":
      return "text-brand-500";
    default:
      return "text-brand-400";
  }
}

export const FINDING_SEVERITIES: FindingSeverity[] = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
];

export type FindingStatusGroup = "" | "open" | "resolved" | "ignored";

export type FindingSortField = "risk_score" | "severity" | "title" | "created_at";
