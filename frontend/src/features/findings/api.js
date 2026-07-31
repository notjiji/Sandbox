import { apiRequest } from "@/shared/api/client";

const base = (projectId) => `/projects/${projectId}/findings`;

export const findingsApi = {
  list: (projectId) => apiRequest(base(projectId), { auth: true }),
  get: (projectId, findingId) =>
    apiRequest(`${base(projectId)}/${findingId}`, { auth: true }),
  update: (projectId, findingId, data) =>
    apiRequest(`${base(projectId)}/${findingId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
};
