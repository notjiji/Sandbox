import { apiRequest } from "@/shared/api/client";
import type {
  CreateScanRequest,
  ScanListData,
  ScanProfilesData,
  ScanSummary,
} from "@/shared/types/scan";

const base = (projectId: string, assetId: string) =>
  `/projects/${projectId}/assets/${assetId}/scans`;

export const scansApi = {
  list: (projectId: string, assetId: string) =>
    apiRequest<ScanListData>(base(projectId, assetId), { auth: true }),

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
