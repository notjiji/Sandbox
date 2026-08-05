export type ReportStatus = "draft" | "generating" | "ready" | "failed";
export type ReportType = "executive" | "technical" | "weekly" | "monthly";

export interface ReportSummary {
  id: string;
  project_id: string;
  asset_id?: string | null;
  report_type: ReportType;
  name: string;
  description?: string | null;
  status: ReportStatus;
  file_url?: string | null;
  created_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ReportListQuery {
  page?: number;
  limit?: number;
  report_type?: ReportType | "";
  status?: ReportStatus | "";
  search?: string;
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
}

export interface CreateAssetReportRequest {
  report_type: ReportType;
  name?: string;
  description?: string | null;
  generate?: boolean;
}

export interface UpdateReportRequest {
  name?: string;
  description?: string | null;
}
