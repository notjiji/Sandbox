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
