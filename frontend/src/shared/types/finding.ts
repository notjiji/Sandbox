export type FindingSeverity = "critical" | "high" | "medium" | "low" | "info";
export type FindingStatus =
  | "open"
  | "in_review"
  | "accepted"
  | "resolved"
  | "false_positive";

export interface FindingSummary {
  id: string;
  project_id: string;
  asset_id: string;
  scan_id?: string | null;
  source?: string;
  finding_code?: string | null;
  title: string;
  description?: string | null;
  severity: FindingSeverity;
  status: FindingStatus;
  risk_score?: number | null;
  detected_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface FindingListQuery {
  page?: number;
  limit?: number;
  status_group?: "" | "open" | "resolved" | "ignored";
  severity?: FindingSeverity | "";
  search?: string;
  sort?: "risk_score" | "severity" | "title" | "created_at";
  order?: "asc" | "desc";
}

export interface FindingListData {
  items: FindingSummary[];
  total: number;
  page: number;
  limit: number;
}

export interface UpdateFindingRequest {
  status?: FindingStatus;
}
