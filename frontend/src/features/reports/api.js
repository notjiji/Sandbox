import { apiRequest } from "@/shared/api/client";

const base = (projectId) => `/projects/${projectId}/reports`;

export const reportsApi = {
  list: (projectId) => apiRequest(base(projectId), { auth: true }),
  create: (projectId, data) =>
    apiRequest(base(projectId), { method: "POST", body: data, auth: true }),
  get: (projectId, reportId) => apiRequest(`${base(projectId)}/${reportId}`, { auth: true }),
  update: (projectId, reportId, data) =>
    apiRequest(`${base(projectId)}/${reportId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
  generate: (projectId, reportId) =>
    apiRequest(`${base(projectId)}/${reportId}/generate`, { method: "POST", auth: true }),
  delete: (projectId, reportId) =>
    apiRequest(`${base(projectId)}/${reportId}`, { method: "DELETE", auth: true }),
};
