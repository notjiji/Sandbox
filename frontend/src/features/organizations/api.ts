import { apiRequest } from "@/shared/api/client";
import type {
  CreateOrganizationRequest,
  OrganizationDetail,
  OrganizationListData,
  UpdateOrganizationRequest,
} from "@/shared/types/organization";
import type { MessageResponse } from "@/shared/types/auth";

export const organizationsApi = {
  listMine: () =>
    apiRequest<OrganizationListData>("/organizations/me", { auth: true }),

  create: (data: CreateOrganizationRequest) =>
    apiRequest<OrganizationDetail>("/organizations", {
      method: "POST",
      body: data,
      auth: true,
    }),

  getCurrent: () =>
    apiRequest<OrganizationDetail>("/organizations/current", { auth: true }),

  updateCurrent: (data: UpdateOrganizationRequest) =>
    apiRequest<OrganizationDetail>("/organizations/current", {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  deleteCurrent: () =>
    apiRequest<MessageResponse>("/organizations/current", {
      method: "DELETE",
      auth: true,
    }),
};
