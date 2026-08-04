import { apiRequest } from "@/shared/api/client";
import type { UpdateUserProfileRequest, UserProfile } from "@/shared/types/user";

export const usersApi = {
  getMe: () => apiRequest<UserProfile>("/users/me", { auth: true }),

  updateMe: (data: UpdateUserProfileRequest) =>
    apiRequest<UserProfile>("/users/me", {
      method: "PATCH",
      body: data,
      auth: true,
    }),
};
