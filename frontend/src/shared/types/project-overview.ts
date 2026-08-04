import type { AuditLogSummary, RecentReportSummary, RecentScanSummary, UsagePlaceholder } from "./organization-overview";
import type { ProjectSummary } from "./project";
import type { ProjectRisk } from "./risk";

export interface ProjectStats {
  assets: number;
  scans: number;
  open_findings: number;
  total_findings: number;
  reports: number;
}

export interface ProjectOverview {
  project: ProjectSummary;
  stats: ProjectStats;
  security: ProjectRisk;
  recent_scans: RecentScanSummary[];
  recent_reports: RecentReportSummary[];
  recent_activity: AuditLogSummary[];
  ai_summary: UsagePlaceholder;
}

export interface ProjectActivityData {
  items: AuditLogSummary[];
  total: number;
  page: number;
  limit: number;
}
