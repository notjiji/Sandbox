import type { DashboardMetrics } from "./risk";
import type { ActivityEvent } from "./activity";

export interface OrganizationTrends {
  assets: number;
  members: number;
  projects: number;
  scans: number;
  reports: number;
  critical_findings: number;
  average_risk?: number | null;
}

export interface OrganizationAnalytics {
  average_risk?: number | null;
  period_days: number;
  trends: OrganizationTrends;
}

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
  entity_type?: string | null;
  entity_id?: string | null;
  severity?: string;
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
  analytics: OrganizationAnalytics;
  security: DashboardMetrics;
  recent_scans: RecentScanSummary[];
  recent_reports: RecentReportSummary[];
  recent_activity: ActivityEvent[];
  storage: UsagePlaceholder;
  api_usage: UsagePlaceholder;
  subscription: UsagePlaceholder;
}
