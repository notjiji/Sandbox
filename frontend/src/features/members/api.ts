import { apiRequest } from "@/shared/api/client";
import type {
  InviteLinkResponse,
  InviteListData,
  InviteMemberRequest,
  InvitePreview,
  MemberListData,
  MemberListQuery,
  MemberSummary,
  RolesListData,
  UpdateMemberRequest,
} from "@/shared/types/member";
import type { MessageResponse } from "@/shared/types/auth";
import type { OrganizationSummary } from "@/shared/types/organization";

function toQuery(params: MemberListQuery): string {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.search) searchParams.set("search", params.search);
  if (params.status) searchParams.set("status", params.status);
  if (params.role) searchParams.set("role", params.role);
  if (params.sort) searchParams.set("sort", params.sort);
  if (params.order) searchParams.set("order", params.order);
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export const membersApi = {
  listMembers: (params: MemberListQuery = {}) =>
    apiRequest<MemberListData>(`/organizations/current/members${toQuery(params)}`, {
      auth: true,
    }),

  listInvites: () =>
    apiRequest<InviteListData>("/organizations/current/invites", { auth: true }),

  inviteMember: (data: InviteMemberRequest) =>
    apiRequest<MemberSummary>("/organizations/current/members", {
      method: "POST",
      body: data,
      auth: true,
    }),

  acceptInvitation: (organizationId: string) =>
    apiRequest<MessageResponse>("/organizations/current/members/accept", {
      method: "POST",
      auth: true,
      organizationId,
    }),

  updateMember: (membershipId: string, data: UpdateMemberRequest) =>
    apiRequest<MemberSummary>(`/organizations/current/members/${membershipId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  removeMember: (membershipId: string) =>
    apiRequest<MessageResponse>(`/organizations/current/members/${membershipId}`, {
      method: "DELETE",
      auth: true,
    }),

  revokeInvite: (inviteId: string) =>
    apiRequest<MessageResponse>(`/organizations/current/invites/${inviteId}`, {
      method: "DELETE",
      auth: true,
    }),

  resendInvite: (inviteId: string, sendEmail = true) =>
    apiRequest<InviteLinkResponse>(
      `/organizations/current/invites/${inviteId}/resend?send_email=${sendEmail}`,
      {
        method: "POST",
        auth: true,
      },
    ),

  previewInvite: (token: string) =>
    apiRequest<InvitePreview>(`/organizations/invites/${token}`),

  acceptInviteToken: (token: string) =>
    apiRequest<OrganizationSummary>(`/organizations/invites/${token}/accept`, {
      method: "POST",
      auth: true,
      organizationId: null,
    }),

  listRoles: () => apiRequest<RolesListData>("/organizations/roles"),
};
