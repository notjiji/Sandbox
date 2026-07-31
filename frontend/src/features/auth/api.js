import { apiRequest, refreshAccessToken } from "@/shared/api/client";
import { tokenStorage } from "./storage";
import { orgStorage } from "@/features/organizations/storage";
import { rawApiRequest } from "./api-helpers";

export const authApi = {
  register: (data) => apiRequest("/auth/register", { method: "POST", body: data }),
  verifyEmail: (data) =>
    apiRequest("/auth/verify-email", { method: "POST", body: data }),
  resendVerification: (data) =>
    apiRequest("/auth/resend-verification", { method: "POST", body: data }),
  login: async (data) => {
    const payload = await apiRequest("/auth/login", { method: "POST", body: data });
    tokenStorage.setTokens(payload);
    return payload;
  },
  refresh: () => refreshAccessToken(),
  logout: async () => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      try {
        await rawApiRequest("/auth/logout", {
          method: "POST",
          body: { refresh_token: refreshToken },
        });
      } catch {
        // Clear local session even if revoke fails (expired token, offline, etc.)
      }
    }
    tokenStorage.clear();
    orgStorage.clear();
  },
  forgotPassword: (data) =>
    apiRequest("/auth/forgot-password", {
      method: "POST",
      body: { email: data.email.trim().toLowerCase() },
    }),
  resetPassword: (data) =>
    apiRequest("/auth/reset-password", { method: "POST", body: data }),
  changePassword: (data) =>
    apiRequest("/auth/change-password", { method: "PUT", body: data, auth: true }),
  listSessions: () => apiRequest("/auth/sessions", { auth: true }),
  revokeSession: (sessionId) =>
    apiRequest(`/auth/sessions/${sessionId}`, { method: "DELETE", auth: true }),
  revokeOtherSessions: () =>
    apiRequest("/auth/sessions/revoke-others", { method: "POST", auth: true }),
  revokeAllSessions: () =>
    apiRequest("/auth/sessions/revoke-all", { method: "POST", auth: true }),
};
