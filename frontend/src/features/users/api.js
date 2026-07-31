import { apiRequest } from "@/shared/api/client";

export const usersApi = {
  getMe: () => apiRequest("/users/me", { auth: true }),
  updateMe: (data) =>
    apiRequest("/users/me", { method: "PATCH", body: data, auth: true }),
};
