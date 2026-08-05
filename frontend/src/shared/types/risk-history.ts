export interface RiskHistoryPoint {
  id: string;
  date: string;
  security_score: number;
  total_risk: number;
  grade: string;
  scan_id?: string | null;
  score_delta?: number | null;
  total_risk_delta?: number | null;
}

export interface RiskChangeExplanation {
  delta: number;
  title: string;
  kind: "new" | "resolved" | string;
  finding_id?: string | null;
  severity?: string | null;
}

export interface RiskHistoryChange {
  from_score: number;
  to_score: number;
  from_date: string;
  to_date: string;
  score_delta: number;
  total_risk_delta: number;
  explanations: RiskChangeExplanation[];
}

export interface AssetRiskHistory {
  current: {
    asset_id: string;
    scanned: boolean;
    score?: number | null;
    grade?: string | null;
    total_risk?: number | null;
    calculated_at?: string | null;
  };
  trend: RiskHistoryPoint[];
  latest_change?: RiskHistoryChange | null;
  changes: RiskHistoryChange[];
}
