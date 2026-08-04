import { apiRequest, refreshAccessToken } from "@/shared/api/client";
import type {
  AuthTokens,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  RegisterResponse,
  ResendVerificationRequest,
  ResetPasswordRequest,
  RevokeSessionResponse,
  SessionListResponse,
  VerifyEmailRequest,
} from "@/shared/types/auth";
import { tokenStorage } from "./storage";
import { orgStorage } from "@/features/organizations/storage";
import { rawApiRequest } from "./api-helpers";

export const authApi = {
  register: (data: RegisterRequest) =>
    apiRequest<RegisterResponse>("/auth/register", { method: "POST", body: data }),

  verifyEmail: (data: VerifyEmailRequest) =>
    apiRequest<MessageResponse>("/auth/verify-email", { method: "POST", body: data }),

  resendVerification: (data: ResendVerificationRequest) =>
    apiRequest<MessageResponse>("/auth/resend-verification", {
      method: "POST",
      body: data,
    }),

  login: async (data: LoginRequest): Promise<AuthTokens> => {
    const payload = await apiRequest<AuthTokens>("/auth/login", {
      method: "POST",
      body: data,
    });
    tokenStorage.setTokens(payload);
    return payload;
  },

  refresh: () => refreshAccessToken(),

  logout: async (): Promise<void> => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      try {
        await rawApiRequest<MessageResponse>("/auth/logout", {
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

  forgotPassword: (data: ForgotPasswordRequest) =>
    apiRequest<MessageResponse>("/auth/forgot-password", {
      method: "POST",
      body: { email: data.email.trim().toLowerCase() },
    }),

  resetPassword: (data: ResetPasswordRequest) =>
    apiRequest<MessageResponse>("/auth/reset-password", { method: "POST", body: data }),

  changePassword: (data: ChangePasswordRequest) =>
    apiRequest<MessageResponse>("/auth/change-password", {
      method: "PUT",
      body: data,
      auth: true,
    }),

  listSessions: () => apiRequest<SessionListResponse>("/auth/sessions", { auth: true }),

  revokeSession: (sessionId: string) =>
    apiRequest<RevokeSessionResponse>(`/auth/sessions/${sessionId}`, {
      method: "DELETE",
      auth: true,
    }),

  revokeOtherSessions: () =>
    apiRequest<MessageResponse>("/auth/sessions/revoke-others", {
      method: "POST",
      auth: true,
    }),

  revokeAllSessions: () =>
    apiRequest<MessageResponse>("/auth/sessions/revoke-all", {
      method: "POST",
      auth: true,
    }),
};
