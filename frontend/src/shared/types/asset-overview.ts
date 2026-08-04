import type { AuditLogSummary, RecentReportSummary, UsagePlaceholder } from "./organization-overview";
import type { AssetSummary } from "./asset";
import type { FindingSummary } from "./finding";
import type { AssetRisk, RiskTrendPoint } from "./risk";
import type { ScanSummary } from "./scan";

export interface AssetStats {
  scans: number;
  open_findings: number;
  total_findings: number;
  critical_findings: number;
  reports: number;
}

export interface AssetOverview {
  asset: AssetSummary;
  stats: AssetStats;
  risk: AssetRisk;
  scan_trend: RiskTrendPoint[];
  recent_scans: ScanSummary[];
  top_findings: FindingSummary[];
  recent_reports: RecentReportSummary[];
  recent_activity: AuditLogSummary[];
  ai_summary: UsagePlaceholder;
}
