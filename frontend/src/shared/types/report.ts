export type ReportStatus = "draft" | "generating" | "ready" | "failed";
export type ReportType = "executive" | "technical" | "weekly" | "monthly";

export interface ReportSummary {
  id: string;
  project_id: string;
  project_name?: string | null;
  asset_id?: string | null;
  scan_id?: string | null;
  report_type: ReportType;
  report_version?: number;
  name: string;
  description?: string | null;
  status: ReportStatus;
  file_url?: string | null;
  file_size?: number | null;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  completed_at?: string | null;
}

export interface ReportListQuery {
  page?: number;
  limit?: number;
  report_type?: ReportType | "";
  status?: ReportStatus | "";
  search?: string;
  project_id?: string;
}

export interface ReportDownloadUrl {
  url: string;
  expires_at: string;
  filename: string;
}

export interface ReportListData {
  items: ReportSummary[];
  total: number;
  page?: number;
  limit?: number;
}

export interface CreateReportRequest {
  name?: string;
  description?: string | null;
  report_type?: ReportType;
  scan_id?: string;
  asset_id?: string;
  generate?: boolean;
}

export interface CreateAssetReportRequest {
  report_type: ReportType;
  name?: string;
  description?: string | null;
  scan_id?: string;
  generate?: boolean;
}

export interface UpdateReportRequest {
  name?: string;
  description?: string | null;
}
