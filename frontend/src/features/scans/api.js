import { apiRequest } from "@/shared/api/client";

const base = (projectId, assetId) =>
  `/projects/${projectId}/assets/${assetId}/scans`;

export const scansApi = {
  list: (projectId, assetId) => apiRequest(base(projectId, assetId), { auth: true }),
  create: (projectId, assetId, data) =>
    apiRequest(base(projectId, assetId), { method: "POST", body: data, auth: true }),
  get: (projectId, assetId, scanId) =>
    apiRequest(`${base(projectId, assetId)}/${scanId}`, { auth: true }),
  run: (projectId, assetId, scanId) =>
    apiRequest(`${base(projectId, assetId)}/${scanId}/run`, { method: "POST", auth: true }),
  cancel: (projectId, assetId, scanId) =>
    apiRequest(`${base(projectId, assetId)}/${scanId}/cancel`, { method: "POST", auth: true }),
};
