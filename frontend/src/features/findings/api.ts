import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type {
  FindingListData,
  FindingSummary,
  UpdateFindingRequest,
} from "@/shared/types/finding";

const base = (projectId: string) => `/projects/${projectId}/findings`;

export const findingsApi = {
  list: (projectId: string) =>
    apiRequest<ApiEnvelope<FindingListData>>(base(projectId), { auth: true }),

  get: (projectId: string, findingId: string) =>
    apiRequest<ApiEnvelope<FindingSummary>>(`${base(projectId)}/${findingId}`, {
      auth: true,
    }),

  update: (projectId: string, findingId: string, data: UpdateFindingRequest) =>
    apiRequest<ApiEnvelope<FindingSummary>>(`${base(projectId)}/${findingId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
};
