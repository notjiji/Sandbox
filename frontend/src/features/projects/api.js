import { apiRequest } from "@/shared/api/client";

export const projectsApi = {
  list: () => apiRequest("/projects", { auth: true }),
  create: (data) => apiRequest("/projects", { method: "POST", body: data, auth: true }),
  get: (projectId) => apiRequest(`/projects/${projectId}`, { auth: true }),
  update: (projectId, data) =>
    apiRequest(`/projects/${projectId}`, { method: "PATCH", body: data, auth: true }),
  delete: (projectId) =>
    apiRequest(`/projects/${projectId}`, { method: "DELETE", auth: true }),
};
