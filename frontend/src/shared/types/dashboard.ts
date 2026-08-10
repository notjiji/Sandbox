import type { SeverityBreakdown } from "./risk";

export interface DashboardScore {
  current: number | null;
  previous: number | null;
  change: number | null;
  grade: string | null;
  trend: string;
}

export interface DashboardAssetsSummary {
  total: number;
  websites: number;
  domains: number;
  ips: number;
  servers: number;
}

export interface DashboardLastScan {
  status: string | null;
  timestamp: string | null;
  scan_id: string | null;
  project_id: string | null;
  asset_id: string | null;
  asset_name: string | null;
}

export interface DashboardOverview {
  score: DashboardScore;
  assets: DashboardAssetsSummary;
  findings: SeverityBreakdown;
  last_scan: DashboardLastScan;
  primary_project_id: string | null;
  scanned_assets: number;
  unscanned_assets: number;
  assets_at_risk: number;
  trend: string;
}

export interface DashboardCriticalFinding {
  finding_id: string;
  finding_code: string;
  title: string;
  severity: string;
  risk_score: number;
  asset_id: string;
  asset_name: string;
  project_id: string;
}

export interface DashboardFindingsSummary {
  breakdown: SeverityBreakdown;
  top_findings: DashboardCriticalFinding[];
}

export interface DashboardTopAsset {
  asset_id: string;
  asset_name: string;
  project_id: string;
  score: number | null;
  grade: string | null;
  scanned: boolean;
}

export interface DashboardUpcomingScan {
  schedule_id: string;
  asset_id: string;
  asset_name: string;
  project_id: string;
  scan_type: string;
  preset: string;
  next_run_at: string;
}

export interface DashboardRiskTrend {
  history: import("./risk").RiskTrendPoint[];
}

export interface DashboardActivity {
  items: import("./activity").ActivityEvent[];
  total: number;
}

export interface DashboardTopAssets {
  items: DashboardTopAsset[];
}

export interface DashboardUpcomingScans {
  items: DashboardUpcomingScan[];
}
