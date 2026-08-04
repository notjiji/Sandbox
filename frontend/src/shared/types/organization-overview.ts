import type { DashboardMetrics } from "./risk";

export interface OrganizationStats {
  projects: number;
  assets: number;
  members: number;
  scans: number;
  open_findings: number;
  total_findings: number;
  reports: number;
}

export interface RecentScanSummary {
  id: string;
  project_id: string;
  asset_id: string;
  status: string;
  scan_type: string;
  created_at: string;
}

export interface RecentReportSummary {
  id: string;
  project_id: string;
  name: string;
  status: string;
  created_at: string;
}

export interface AuditLogSummary {
  id: string;
  action: string;
  user_id?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export interface UsagePlaceholder {
  label: string;
  value: string;
  available: boolean;
}

export interface OrganizationOverview {
  stats: OrganizationStats;
  security: DashboardMetrics;
  recent_scans: RecentScanSummary[];
  recent_reports: RecentReportSummary[];
  recent_activity: AuditLogSummary[];
  storage: UsagePlaceholder;
  api_usage: UsagePlaceholder;
  subscription: UsagePlaceholder;
}
