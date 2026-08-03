import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type {
  AssetListData,
  AssetListQuery,
  AssetSummary,
  CreateAssetRequest,
  UpdateAssetRequest,
} from "@/shared/types/asset";

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
    apiRequest<ApiEnvelope<AssetListData>>(`${base(projectId)}${toQuery(params)}`, {
      auth: true,
    }),

  create: (projectId: string, data: CreateAssetRequest) =>
    apiRequest<ApiEnvelope<AssetSummary>>(base(projectId), {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string, assetId: string) =>
    apiRequest<ApiEnvelope<AssetSummary>>(`${base(projectId)}/${assetId}`, { auth: true }),

  update: (projectId: string, assetId: string, data: UpdateAssetRequest) =>
    apiRequest<ApiEnvelope<AssetSummary>>(`${base(projectId)}/${assetId}`, {
      method: "PUT",
      body: data,
      auth: true,
    }),

  archive: (projectId: string, assetId: string) =>
    apiRequest<ApiEnvelope<AssetSummary>>(`${base(projectId)}/${assetId}/archive`, {
      method: "PATCH",
      auth: true,
    }),

  restore: (projectId: string, assetId: string) =>
    apiRequest<ApiEnvelope<AssetSummary>>(`${base(projectId)}/${assetId}/restore`, {
      method: "PATCH",
      auth: true,
    }),

  delete: (projectId: string, assetId: string) =>
    apiRequest<ApiEnvelope<void>>(`${base(projectId)}/${assetId}`, {
      method: "DELETE",
      auth: true,
    }),

  auditHistory: (projectId: string, assetId: string) =>
    apiRequest<ApiEnvelope<unknown>>(`${base(projectId)}/${assetId}/audit-history`, {
      auth: true,
    }),

  children: (projectId: string, assetId: string, params?: AssetListQuery) =>
    apiRequest<ApiEnvelope<AssetListData>>(
      `${base(projectId)}/${assetId}/children${toQuery(params)}`,
      { auth: true },
    ),
};
