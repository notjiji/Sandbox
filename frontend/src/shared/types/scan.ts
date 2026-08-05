export type ScanStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ScanType = "quick" | "full" | "custom";

export interface ScanLifecycleTimestamps {
  pending_at?: string | null;
  queued_at?: string | null;
  running_at?: string | null;
  completed_at?: string | null;
  failed_at?: string | null;
  cancelled_at?: string | null;
}

export interface ScanMetrics {
  duration_seconds?: number | null;
  risk_score?: number | null;
  grade?: string | null;
  critical_count?: number;
  findings_count?: number;
}

export interface ScanPluginRunSummary {
  id: string;
  asset_id: string;
  plugin_name: string;
  status: string;
  error_message?: string | null;
  findings_count?: number;
  duration_seconds?: number | null;
  metadata?: Record<string, unknown>;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface ScanSummary {
  id: string;
  asset_id: string;
  project_id: string;
  scan_type: ScanType;
  status: ScanStatus;
  selected_plugins?: string[];
  profile_plugins?: string[];
  created_by?: string | null;
  created_at?: string | null;
  lifecycle?: ScanLifecycleTimestamps;
  plugin_runs?: ScanPluginRunSummary[];
  metrics?: ScanMetrics;
}

export interface ScanListQuery {
  page?: number;
  limit?: number;
  status?: ScanStatus | "";
  scan_type?: ScanType | "";
  search?: string;
}

export interface ScanListData {
  items: ScanSummary[];
  total: number;
  page: number;
  limit: number;
}

export interface ScanCompareDiff {
  risk_score_delta?: number | null;
  critical_count_delta: number;
  findings_count_delta: number;
  duration_seconds_delta?: number | null;
}

export interface ScanCompareData {
  scan_a: ScanSummary;
  scan_b: ScanSummary;
  diff: ScanCompareDiff;
}

export interface ScanExportFindingSummary {
  id: string;
  title: string;
  severity: string;
  status: string;
  risk_score: number;
  plugin?: string | null;
}

export interface ScanExportData {
  scan: ScanSummary;
  findings: ScanExportFindingSummary[];
  exported_at: string;
}

export interface ScanProfile {
  profile: ScanType;
  label: string;
  description: string;
  plugins: string[];
}

export interface CreateScanRequest {
  scan_type: ScanType;
  plugins?: string[];
}

export interface ScanProfilesData {
  items: ScanProfile[];
}

export type ScanSchedulePreset = "quick_daily" | "full_sunday" | "ssl_12h" | "dns_weekly";

export interface ScanScheduleSummary {
  id: string;
  preset: ScanSchedulePreset;
  label: string;
  cadence: string;
  scan_type: ScanType;
  profile_label: string;
  enabled: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  last_scan_id?: string | null;
}

export interface ScanScheduleListData {
  items: ScanScheduleSummary[];
}

export interface UpdateScanScheduleRequest {
  enabled: boolean;
}
