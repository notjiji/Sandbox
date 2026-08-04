import { apiRequest } from "@/shared/api/client";
import type {
  InviteListData,
  InviteMemberRequest,
  InvitePreview,
  MemberListData,
  MemberSummary,
  RolesListData,
  UpdateMemberRequest,
} from "@/shared/types/member";
import type { MessageResponse } from "@/shared/types/auth";
import type { OrganizationSummary } from "@/shared/types/organization";

export const membersApi = {
  listMembers: () =>
    apiRequest<MemberListData>("/organizations/current/members", { auth: true }),

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
