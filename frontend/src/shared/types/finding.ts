export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";
export type FindingStatus = "open" | "accepted" | "resolved" | "false_positive";

export interface FindingSummary {
  id: string;
  project_id: string;
  asset_id: string;
  scan_id?: string | null;
  finding_code: string;
  title: string;
  severity: FindingSeverity;
  status: FindingStatus;
  risk_score?: number | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateFindingRequest {
  status?: FindingStatus;
}

export interface FindingListData {
  items: FindingSummary[];
}
