import { apiRequest } from "@/shared/api/client";
import type {
  FindingListData,
  FindingListQuery,
  FindingSummary,
  UpdateFindingRequest,
} from "@/shared/types/finding";

const base = (projectId: string) => `/projects/${projectId}/findings`;
const assetBase = (projectId: string, assetId: string) =>
  `/projects/${projectId}/assets/${assetId}/findings`;

function toQuery(params: FindingListQuery = {}): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const findingsApi = {
  list: (projectId: string, params?: FindingListQuery) =>
    apiRequest<FindingListData>(`${base(projectId)}${toQuery(params)}`, { auth: true }),

  listForAsset: (projectId: string, assetId: string, params?: FindingListQuery) =>
    apiRequest<FindingListData>(
      `${assetBase(projectId, assetId)}${toQuery(params)}`,
      { auth: true },
    ),

  get: (projectId: string, findingId: string) =>
    apiRequest<FindingSummary>(`${base(projectId)}/${findingId}`, {
      auth: true,
    }),

  update: (projectId: string, findingId: string, data: UpdateFindingRequest) =>
    apiRequest<FindingSummary>(`${base(projectId)}/${findingId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  updateForAsset: (
    projectId: string,
    assetId: string,
    findingId: string,
    data: UpdateFindingRequest,
  ) =>
    apiRequest<FindingSummary>(`${assetBase(projectId, assetId)}/${findingId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
};
