import { apiRequest } from "@/shared/api/client";

const base = (projectId) => `/projects/${projectId}/assets`;

function toQuery(params = {}) {
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
  list: (projectId, params) =>
    apiRequest(`${base(projectId)}${toQuery(params)}`, { auth: true }),
  create: (projectId, data) =>
    apiRequest(base(projectId), { method: "POST", body: data, auth: true }),
  get: (projectId, assetId) => apiRequest(`${base(projectId)}/${assetId}`, { auth: true }),
  update: (projectId, assetId, data) =>
    apiRequest(`${base(projectId)}/${assetId}`, { method: "PUT", body: data, auth: true }),
  archive: (projectId, assetId) =>
    apiRequest(`${base(projectId)}/${assetId}/archive`, { method: "PATCH", auth: true }),
  restore: (projectId, assetId) =>
    apiRequest(`${base(projectId)}/${assetId}/restore`, { method: "PATCH", auth: true }),
  delete: (projectId, assetId) =>
    apiRequest(`${base(projectId)}/${assetId}`, { method: "DELETE", auth: true }),
};
