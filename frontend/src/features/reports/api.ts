import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type {
  CreateReportRequest,
  ReportListData,
  ReportSummary,
  UpdateReportRequest,
} from "@/shared/types/report";

const base = (projectId: string) => `/projects/${projectId}/reports`;

export const reportsApi = {
  list: (projectId: string) =>
    apiRequest<ApiEnvelope<ReportListData>>(base(projectId), { auth: true }),

  create: (projectId: string, data: CreateReportRequest) =>
    apiRequest<ApiEnvelope<ReportSummary>>(base(projectId), {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string, reportId: string) =>
    apiRequest<ApiEnvelope<ReportSummary>>(`${base(projectId)}/${reportId}`, { auth: true }),

  update: (projectId: string, reportId: string, data: UpdateReportRequest) =>
    apiRequest<ApiEnvelope<ReportSummary>>(`${base(projectId)}/${reportId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  generate: (projectId: string, reportId: string) =>
    apiRequest<ApiEnvelope<ReportSummary>>(`${base(projectId)}/${reportId}/generate`, {
      method: "POST",
      auth: true,
    }),

  delete: (projectId: string, reportId: string) =>
    apiRequest<ApiEnvelope<void>>(`${base(projectId)}/${reportId}`, {
      method: "DELETE",
      auth: true,
    }),
};
