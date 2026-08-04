import { apiRequest } from "@/shared/api/client";
import type {
  AssetListData,
  AssetListQuery,
  AssetLinkSummary,
  AssetRelationships,
  AssetSummary,
  CreateAssetLinkRequest,
  CreateAssetRequest,
  UpdateAssetRequest,
} from "@/shared/types/asset";
import type { AssetOverview } from "@/shared/types/asset-overview";

const base = (projectId: string) => `/projects/${projectId}/assets`;

function toQuery(params: AssetListQuery = {}): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
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
};
