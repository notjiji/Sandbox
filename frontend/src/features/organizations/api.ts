import { apiRequest } from "@/shared/api/client";
import type {
  CreateOrganizationRequest,
  OrganizationDetail,
  OrganizationListData,
  UpdateOrganizationRequest,
} from "@/shared/types/organization";
import type { ActivityFilters, OrganizationActivityData } from "@/shared/types/activity";
import type { OrganizationOverview } from "@/shared/types/organization-overview";
import type { MessageResponse } from "@/shared/types/auth";

function activityQuery(page: number, limit: number, filters?: ActivityFilters): string {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (!filters) return params.toString();
  const entries: Array<[keyof ActivityFilters, string | undefined]> = [
    ["action", filters.action],
    ["actor", filters.actor],
    ["asset_id", filters.asset_id],
    ["severity", filters.severity],
    ["date_from", filters.date_from],
    ["date_to", filters.date_to],
  ];
  for (const [key, value] of entries) {
    if (value?.trim()) params.set(key, value.trim());
  }
  return params.toString();
}

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

  getActivity: (page = 1, limit = 20, filters?: ActivityFilters) =>
    apiRequest<OrganizationActivityData>(
      `/organizations/current/activity?${activityQuery(page, limit, filters)}`,
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
