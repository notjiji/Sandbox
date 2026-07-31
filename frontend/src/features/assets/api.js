import { apiRequest } from "@/shared/api/client";

const base = (projectId) => `/projects/${projectId}/assets`;

export const assetsApi = {
  list: (projectId) => apiRequest(base(projectId), { auth: true }),
  create: (projectId, data) =>
    apiRequest(base(projectId), { method: "POST", body: data, auth: true }),
  get: (projectId, assetId) => apiRequest(`${base(projectId)}/${assetId}`, { auth: true }),
  update: (projectId, assetId, data) =>
    apiRequest(`${base(projectId)}/${assetId}`, { method: "PATCH", body: data, auth: true }),
  delete: (projectId, assetId) =>
    apiRequest(`${base(projectId)}/${assetId}`, { method: "DELETE", auth: true }),
};
