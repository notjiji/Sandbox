import { apiRequest } from "@/shared/api/client";
import type {
  CreateOrganizationRequest,
  OrganizationDetail,
  OrganizationListData,
  UpdateOrganizationRequest,
} from "@/shared/types/organization";
import type { OrganizationActivityData } from "@/shared/types/activity";
import type { OrganizationOverview } from "@/shared/types/organization-overview";
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

  getOverview: () =>
    apiRequest<OrganizationOverview>("/organizations/current/overview", { auth: true }),

  getActivity: (page = 1, limit = 20) =>
    apiRequest<OrganizationActivityData>(
      `/organizations/current/activity?page=${page}&limit=${limit}`,
      { auth: true },
    ),

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

  archiveCurrent: () =>
    apiRequest<OrganizationDetail>("/organizations/current/archive", {
      method: "PATCH",
      auth: true,
    }),

  restore: (organizationId: string) =>
    apiRequest<OrganizationDetail>(`/organizations/${organizationId}/restore`, {
      method: "PATCH",
      auth: true,
    }),
};
