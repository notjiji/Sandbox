export type ReportStatus = "draft" | "generating" | "ready" | "failed";

export interface ReportSummary {
  id: string;
  project_id: string;
  title: string;
  status: ReportStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateReportRequest {
  title: string;
}

export interface UpdateReportRequest {
  title?: string;
}

export interface ReportListData {
  items: ReportSummary[];
}
