import { apiRequest } from "@/shared/api/client";

const base = (projectId) => `/projects/${projectId}/scans`;

export const scansApi = {
  list: (projectId) => apiRequest(base(projectId), { auth: true }),
  create: (projectId, data) =>
    apiRequest(base(projectId), { method: "POST", body: data, auth: true }),
  get: (projectId, scanId) => apiRequest(`${base(projectId)}/${scanId}`, { auth: true }),
  run: (projectId, scanId) =>
    apiRequest(`${base(projectId)}/${scanId}/run`, { method: "POST", auth: true }),
  cancel: (projectId, scanId) =>
    apiRequest(`${base(projectId)}/${scanId}/cancel`, { method: "POST", auth: true }),
};
