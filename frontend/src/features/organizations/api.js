import { apiRequest } from "@/shared/api/client";

export const organizationsApi = {
  listMine: () => apiRequest("/organizations/me", { auth: true }),
  create: (data) =>
    apiRequest("/organizations", { method: "POST", body: data, auth: true }),
  getCurrent: () => apiRequest("/organizations/current", { auth: true }),
  updateCurrent: (data) =>
    apiRequest("/organizations/current", { method: "PATCH", body: data, auth: true }),
  deleteCurrent: () =>
    apiRequest("/organizations/current", { method: "DELETE", auth: true }),
};
