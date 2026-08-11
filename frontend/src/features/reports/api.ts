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

async function fetchBinaryOrText(path: string, accept: string): Promise<Response> {
  const headers: Record<string, string> = { Accept: accept };
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

  return response;
}

async function downloadPdf(path: string, filename: string): Promise<void> {
  const response = await fetchBinaryOrText(path, "application/pdf");
  if (!response.ok) throw new Error("Unable to download report.");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function fetchPreviewHtml(path: string): Promise<string> {
  const response = await fetchBinaryOrText(path, "text/html");
  if (!response.ok) throw new Error("Unable to load report preview.");
  return response.text();
}

export const reportsApi = {
  listForOrganization: (params?: ReportListQuery) =>
    apiRequest<ReportListData>(`/organizations/current/reports${toQuery(params)}`, { auth: true }),

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

  regenerate: (projectId: string, reportId: string) =>
    apiRequest<ReportSummary>(`${projectBase(projectId)}/${reportId}/regenerate`, {
      method: "POST",
      auth: true,
    }),

  regenerateForAsset: (projectId: string, assetId: string, reportId: string) =>
    apiRequest<ReportSummary>(`${assetBase(projectId, assetId)}/${reportId}/regenerate`, {
      method: "POST",
      auth: true,
    }),

  previewHtml: (projectId: string, reportId: string) =>
    fetchPreviewHtml(`${projectBase(projectId)}/${reportId}/preview`),

  previewHtmlForAsset: (projectId: string, assetId: string, reportId: string) =>
    fetchPreviewHtml(`${assetBase(projectId, assetId)}/${reportId}/preview`),

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
