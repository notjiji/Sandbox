import { apiRequest, refreshAccessToken } from "@/shared/api/client";
import { orgStorage } from "@/features/organizations/storage";
import { tokenStorage } from "@/features/auth/storage";
import type {
  CreateAssetReportRequest,
  CreateReportRequest,
  ReportListData,
  ReportListQuery,
  ReportSummary,
  UpdateReportRequest,
} from "@/shared/types/report";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const projectBase = (projectId: string) => `/projects/${projectId}/reports`;
const assetBase = (projectId: string, assetId: string) =>
  `/projects/${projectId}/assets/${assetId}/reports`;

function toQuery(params: ReportListQuery = {}): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

async function downloadPdf(path: string, filename: string): Promise<void> {
  const headers: Record<string, string> = {};
  const accessToken = tokenStorage.getAccessToken();
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const orgId = orgStorage.getActiveOrgId();
  if (orgId) headers["X-Organization-ID"] = orgId;

  let response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers,
  });

  if (response.status === 401 && tokenStorage.getRefreshToken()) {
    await refreshAccessToken();
    const refreshed = tokenStorage.getAccessToken();
    if (refreshed) headers.Authorization = `Bearer ${refreshed}`;
    response = await fetch(`${API_BASE_URL}${path}`, {
      credentials: "include",
      headers,
    });
  }

  if (!response.ok) {
    throw new Error("Unable to download report.");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const reportsApi = {
  list: (projectId: string, params?: ReportListQuery) =>
    apiRequest<ReportListData>(`${projectBase(projectId)}${toQuery(params)}`, { auth: true }),

  listForAsset: (projectId: string, assetId: string, params?: ReportListQuery) =>
    apiRequest<ReportListData>(
      `${assetBase(projectId, assetId)}${toQuery(params)}`,
      { auth: true },
    ),

  create: (projectId: string, data: CreateReportRequest) =>
    apiRequest<ReportSummary>(projectBase(projectId), {
      method: "POST",
      body: data,
      auth: true,
    }),

  createForAsset: (projectId: string, assetId: string, data: CreateAssetReportRequest) =>
    apiRequest<ReportSummary>(assetBase(projectId, assetId), {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string, reportId: string) =>
    apiRequest<ReportSummary>(`${projectBase(projectId)}/${reportId}`, { auth: true }),

  update: (projectId: string, reportId: string, data: UpdateReportRequest) =>
    apiRequest<ReportSummary>(`${projectBase(projectId)}/${reportId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  generate: (projectId: string, reportId: string) =>
    apiRequest<ReportSummary>(`${projectBase(projectId)}/${reportId}/generate`, {
      method: "POST",
      auth: true,
    }),

  generateForAsset: (projectId: string, assetId: string, reportId: string) =>
    apiRequest<ReportSummary>(`${assetBase(projectId, assetId)}/${reportId}/generate`, {
      method: "POST",
      auth: true,
    }),

  download: (projectId: string, reportId: string, filename: string) =>
    downloadPdf(`${projectBase(projectId)}/${reportId}/download`, filename),

  downloadForAsset: (
    projectId: string,
    assetId: string,
    reportId: string,
    filename: string,
  ) => downloadPdf(`${assetBase(projectId, assetId)}/${reportId}/download`, filename),

  delete: (projectId: string, reportId: string) =>
    apiRequest<void>(`${projectBase(projectId)}/${reportId}`, {
      method: "DELETE",
      auth: true,
    }),
};
