import { apiRequest } from "@/shared/api/client";
import type {
  AssetListData,
  AssetListQuery,
  AssetLinkSummary,
  AssetRelationships,
  AssetSavedFilterListData,
  AssetSavedFilterSummary,
  AssetSummary,
  AssetTagListData,
  CreateAssetLinkRequest,
  CreateAssetRequest,
  CreateAssetSavedFilterRequest,
  AssetBulkActionRequest,
  AssetBulkActionResponse,
  UpdateAssetRequest,
} from "@/shared/types/asset";
import type { AssetOverview } from "@/shared/types/asset-overview";
import type { ActivityEvent } from "@/shared/types/activity";
import type { AssetRiskHistory } from "@/shared/types/risk-history";

const base = (projectId: string) => `/projects/${projectId}/assets`;

function toQuery(params: AssetListQuery = {}): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    if (key === "tags" && Array.isArray(value)) {
      if (value.length > 0) search.set("tags", value.join(","));
      return;
    }
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const assetsApi = {
  list: (projectId: string, params?: AssetListQuery) =>
    apiRequest<AssetListData>(`${base(projectId)}${toQuery(params)}`, {
      auth: true,
    }),

  create: (projectId: string, data: CreateAssetRequest) =>
    apiRequest<AssetSummary>(base(projectId), {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string, assetId: string) =>
    apiRequest<AssetSummary>(`${base(projectId)}/${assetId}`, { auth: true }),

  overview: (projectId: string, assetId: string) =>
    apiRequest<AssetOverview>(`${base(projectId)}/${assetId}/overview`, { auth: true }),

  timeline: (projectId: string, assetId: string, limit = 50) =>
    apiRequest<{ items: ActivityEvent[]; total: number }>(
      `${base(projectId)}/${assetId}/timeline?limit=${limit}`,
      { auth: true },
    ),

  riskHistory: (projectId: string, assetId: string, limit = 20) =>
    apiRequest<AssetRiskHistory>(
      `${base(projectId)}/${assetId}/risk-history?limit=${limit}`,
      { auth: true },
    ),

  update: (projectId: string, assetId: string, data: UpdateAssetRequest) =>
    apiRequest<AssetSummary>(`${base(projectId)}/${assetId}`, {
      method: "PUT",
      body: data,
      auth: true,
    }),

  archive: (projectId: string, assetId: string) =>
    apiRequest<AssetSummary>(`${base(projectId)}/${assetId}/archive`, {
      method: "PATCH",
      auth: true,
    }),

  restore: (projectId: string, assetId: string) =>
    apiRequest<AssetSummary>(`${base(projectId)}/${assetId}/restore`, {
      method: "PATCH",
      auth: true,
    }),

  delete: (projectId: string, assetId: string) =>
    apiRequest<void>(`${base(projectId)}/${assetId}`, {
      method: "DELETE",
      auth: true,
    }),

  auditHistory: (projectId: string, assetId: string) =>
    apiRequest<unknown>(`${base(projectId)}/${assetId}/audit-history`, {
      auth: true,
    }),

  children: (projectId: string, assetId: string, params?: AssetListQuery) =>
    apiRequest<AssetListData>(
      `${base(projectId)}/${assetId}/children${toQuery(params)}`,
      { auth: true },
    ),

  relationships: (projectId: string, assetId: string) =>
    apiRequest<AssetRelationships>(`${base(projectId)}/${assetId}/relationships`, {
      auth: true,
    }),

  createLink: (projectId: string, assetId: string, data: CreateAssetLinkRequest) =>
    apiRequest<AssetLinkSummary>(`${base(projectId)}/${assetId}/links`, {
      method: "POST",
      body: data,
      auth: true,
    }),

  deleteLink: (projectId: string, assetId: string, linkId: string) =>
    apiRequest<void>(`${base(projectId)}/${assetId}/links/${linkId}`, {
      method: "DELETE",
      auth: true,
    }),

  tags: (projectId: string) =>
    apiRequest<AssetTagListData>(`${base(projectId)}/tags`, { auth: true }),

  savedFilters: (projectId: string) =>
    apiRequest<AssetSavedFilterListData>(`${base(projectId)}/saved-filters`, {
      auth: true,
    }),

  createSavedFilter: (projectId: string, data: CreateAssetSavedFilterRequest) =>
    apiRequest<AssetSavedFilterSummary>(`${base(projectId)}/saved-filters`, {
      method: "POST",
      body: data,
      auth: true,
    }),

  deleteSavedFilter: (projectId: string, filterId: string) =>
    apiRequest<void>(`${base(projectId)}/saved-filters/${filterId}`, {
      method: "DELETE",
      auth: true,
    }),

  bulk: (projectId: string, data: AssetBulkActionRequest) =>
    apiRequest<AssetBulkActionResponse>(`${base(projectId)}/bulk`, {
      method: "POST",
      body: data,
      auth: true,
    }),
};
