import { apiRequest } from "@/shared/api/client";
import type {
  FindingListData,
  FindingSummary,
  UpdateFindingRequest,
} from "@/shared/types/finding";

const base = (projectId: string) => `/projects/${projectId}/findings`;

export const findingsApi = {
  list: (projectId: string) =>
    apiRequest<FindingListData>(base(projectId), { auth: true }),

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
};
