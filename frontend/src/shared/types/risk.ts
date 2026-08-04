export interface SeverityBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface PrioritizedFinding {
  finding_id: string;
  finding_code: string;
  title: string;
  severity: string;
  risk_score: number;
  recommendation_id?: string | null;
  asset_id: string;
  asset_criticality?: string | null;
}

export interface ProjectRisk {
  project_id: string;
  total_risk: number;
  security_score: number;
  grade: string;
  risk_level: string;
  open_findings: number;
  breakdown: SeverityBreakdown;
  top_issues: PrioritizedFinding[];
  calculated_at?: string | null;
}

export interface AssetRisk {
  asset_id: string;
  scanned: boolean;
  scan_id?: string | null;
  total_risk?: number | null;
  score?: number | null;
  grade?: string | null;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  calculated_at?: string | null;
}

export interface RiskTrendPoint {
  date: string;
  security_score: number;
  grade: string;
  total_risk: number;
}

export interface DashboardMetrics {
  overall_security_score?: number | null;
  organization_grade?: string | null;
  risk_level?: string | null;
  trend: string;
  total_findings: number;
  critical_findings: number;
  high_findings: number;
  assets_at_risk: number;
  unscanned_assets: number;
  most_common_issue?: string | null;
  average_days_between_scans?: number | null;
  findings_by_plugin: Record<string, number>;
  findings_by_asset_type: Record<string, number>;
  risk_trend: RiskTrendPoint[];
}
