export type ScanStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ScanType = "quick" | "full" | "custom";

export interface ScanSummary {
  id: string;
  asset_id: string;
  project_id: string;
  scan_type: ScanType;
  status: ScanStatus;
  selected_plugins?: string[] | null;
  created_at: string;
  pending_at?: string | null;
  queued_at?: string | null;
  running_at?: string | null;
  completed_at?: string | null;
  failed_at?: string | null;
  cancelled_at?: string | null;
}

export interface ScanProfile {
  scan_type: ScanType;
  label: string;
  description: string;
  plugins: string[];
}

export interface CreateScanRequest {
  scan_type: ScanType;
  plugins?: string[];
}

export interface ScanListData {
  items: ScanSummary[];
}

export interface ScanProfilesData {
  profiles: ScanProfile[];
}
