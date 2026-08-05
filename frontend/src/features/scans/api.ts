import { apiRequest } from "@/shared/api/client";
import type {
  CreateScanRequest,
  ScanCompareData,
  ScanExportData,
  ScanListData,
  ScanListQuery,
  ScanProfilesData,
  ScanSummary,
} from "@/shared/types/scan";

const base = (projectId: string, assetId: string) =>
  `/projects/${projectId}/assets/${assetId}/scans`;

function toQuery(params: ScanListQuery = {}): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const scansApi = {
  list: (projectId: string, assetId: string, params?: ScanListQuery) =>
    apiRequest<ScanListData>(`${base(projectId, assetId)}${toQuery(params)}`, {
      auth: true,
    }),

  profiles: (projectId: string, assetId: string) =>
    apiRequest<ScanProfilesData>(`${base(projectId, assetId)}/profiles`, {
      auth: true,
    }),

  create: (projectId: string, assetId: string, data: CreateScanRequest) =>
    apiRequest<ScanSummary>(base(projectId, assetId), {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string, assetId: string, scanId: string) =>
    apiRequest<ScanSummary>(`${base(projectId, assetId)}/${scanId}`, {
      auth: true,
    }),

  compare: (projectId: string, assetId: string, scanA: string, scanB: string) =>
    apiRequest<ScanCompareData>(
      `${base(projectId, assetId)}/compare?scan_a=${scanA}&scan_b=${scanB}`,
      { auth: true },
    ),

  export: (projectId: string, assetId: string, scanId: string) =>
    apiRequest<ScanExportData>(`${base(projectId, assetId)}/${scanId}/export`, {
      auth: true,
    }),

  run: (projectId: string, assetId: string, scanId: string) =>
    apiRequest<ScanSummary>(`${base(projectId, assetId)}/${scanId}/run`, {
      method: "POST",
      auth: true,
    }),

  cancel: (projectId: string, assetId: string, scanId: string) =>
    apiRequest<ScanSummary>(`${base(projectId, assetId)}/${scanId}/cancel`, {
      method: "POST",
      auth: true,
    }),
};

export async function downloadScanReport(
  projectId: string,
  assetId: string,
  scanId: string,
): Promise<void> {
  const payload = await scansApi.export(projectId, assetId, scanId);
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `scan-${scanId.slice(0, 8)}-report.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}
