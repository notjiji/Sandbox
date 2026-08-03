import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type { UpdateUserProfileRequest, UserProfile } from "@/shared/types/user";

export const usersApi = {
  getMe: () => apiRequest<ApiEnvelope<UserProfile>>("/users/me", { auth: true }),

  updateMe: (data: UpdateUserProfileRequest) =>
    apiRequest<ApiEnvelope<UserProfile>>("/users/me", {
      method: "PATCH",
      body: data,
      auth: true,
    }),
};
