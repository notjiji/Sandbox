import { apiRequest } from "@/shared/api/client";

export const membersApi = {
  listMembers: () => apiRequest("/organizations/current/members", { auth: true }),
  listInvites: () => apiRequest("/organizations/current/invites", { auth: true }),
  inviteMember: (data) =>
    apiRequest("/organizations/current/members", {
      method: "POST",
      body: data,
      auth: true,
    }),
  acceptInvitation: (organizationId) =>
    apiRequest("/organizations/current/members/accept", {
      method: "POST",
      auth: true,
      organizationId,
    }),
  updateMember: (membershipId, data) =>
    apiRequest(`/organizations/current/members/${membershipId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
  removeMember: (membershipId) =>
    apiRequest(`/organizations/current/members/${membershipId}`, {
      method: "DELETE",
      auth: true,
    }),
  revokeInvite: (inviteId) =>
    apiRequest(`/organizations/current/invites/${inviteId}`, {
      method: "DELETE",
      auth: true,
    }),
  previewInvite: (token) => apiRequest(`/organizations/invites/${token}`),
  acceptInviteToken: (token) =>
    apiRequest(`/organizations/invites/${token}/accept`, {
      method: "POST",
      auth: true,
      organizationId: null,
    }),
  listRoles: () => apiRequest("/organizations/roles"),
};
