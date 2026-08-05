import type { ReportType } from "@/shared/types/report";

export const REPORT_TYPES: { value: ReportType; label: string; description: string }[] = [
  {
    value: "executive",
    label: "Executive",
    description: "High-level risk summary for leadership.",
  },
  {
    value: "technical",
    label: "Technical",
    description: "Detailed findings with remediation guidance.",
  },
  {
    value: "weekly",
    label: "Weekly",
    description: "Weekly snapshot of asset security posture.",
  },
  {
    value: "monthly",
    label: "Monthly",
    description: "Monthly trend and findings overview.",
  },
];

export function reportTypeLabel(type: ReportType | string): string {
  return REPORT_TYPES.find((item) => item.value === type)?.label ?? String(type);
}

export function statusLabel(status: string): string {
  switch (status) {
    case "draft":
      return "Draft";
    case "generating":
      return "Generating";
    case "ready":
      return "Ready";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

export function statusClass(status: string): string {
  switch (status) {
    case "ready":
      return "text-emerald-300";
    case "generating":
      return "text-yellow-300";
    case "failed":
      return "text-red-300";
    default:
      return "text-brand-400";
  }
}
