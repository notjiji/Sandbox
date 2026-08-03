import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type {
  CreateOrganizationRequest,
  OrganizationDetail,
  OrganizationListData,
  UpdateOrganizationRequest,
} from "@/shared/types/organization";
import type { MessageResponse } from "@/shared/types/auth";

export const organizationsApi = {
  listMine: () =>
    apiRequest<ApiEnvelope<OrganizationListData>>("/organizations/me", { auth: true }),

  create: (data: CreateOrganizationRequest) =>
    apiRequest<ApiEnvelope<OrganizationDetail>>("/organizations", {
      method: "POST",
      body: data,
      auth: true,
    }),

  getCurrent: () =>
    apiRequest<ApiEnvelope<OrganizationDetail>>("/organizations/current", { auth: true }),

  updateCurrent: (data: UpdateOrganizationRequest) =>
    apiRequest<ApiEnvelope<OrganizationDetail>>("/organizations/current", {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  deleteCurrent: () =>
    apiRequest<ApiEnvelope<MessageResponse>>("/organizations/current", {
      method: "DELETE",
      auth: true,
    }),
};
