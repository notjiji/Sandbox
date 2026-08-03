import { orgStorage } from "./storage";
import type { ApiEnvelope } from "@/shared/types/api";
import type { OrganizationListData, OrganizationSummary } from "@/shared/types/organization";

interface OrganizationsApiClient {
  listMine: () => Promise<ApiEnvelope<OrganizationListData>>;
}

function normalizeOrganizations(
  payload: ApiEnvelope<OrganizationListData> | OrganizationListData,
): OrganizationSummary[] {
  if ("data" in payload && payload.data?.items) {
    return payload.data.items;
  }
  if ("items" in payload && payload.items) {
    return payload.items;
  }
  return [];
}

/** Only organizations where the user has an active membership. */
export function getActiveOrganizations(
  payload: ApiEnvelope<OrganizationListData> | OrganizationListData,
): OrganizationSummary[] {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "active" && org.is_active,
  );
}

export function getInvitedOrganizations(
  payload: ApiEnvelope<OrganizationListData> | OrganizationListData,
): OrganizationSummary[] {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "invited" && org.is_active,
  );
}

/**
 * Validate stored org id against server membership list.
 * Never trust a client-side org id without this check.
 */
export function resolveActiveOrganization(
  organizationsPayload: ApiEnvelope<OrganizationListData> | OrganizationListData,
): string | null {
  const activeOrgs = getActiveOrganizations(organizationsPayload);
  if (!activeOrgs.length) {
    orgStorage.clear();
    return null;
  }

  const current = orgStorage.getActiveOrgId();
  const match = activeOrgs.find((org) => org.id === current);
  if (match) return match.id;

  const firstOrg = activeOrgs[0];
  if (!firstOrg) return null;

  orgStorage.setActiveOrgId(firstOrg.id);
  return firstOrg.id;
}

export async function syncOrganizations(api: OrganizationsApiClient) {
  const payload = await api.listMine();
  const activeOrgId = resolveActiveOrganization(payload);
  return {
    payload,
    activeOrgId,
    activeOrganizations: getActiveOrganizations(payload),
    invitedOrganizations: getInvitedOrganizations(payload),
  };
}

export function setValidatedActiveOrg(
  organizationId: string,
  organizationsPayload: ApiEnvelope<OrganizationListData> | OrganizationListData,
): OrganizationSummary {
  const activeOrgs = getActiveOrganizations(organizationsPayload);
  const match = activeOrgs.find((org) => org.id === organizationId);
  if (!match) {
    throw new Error("Organization not found in your active memberships");
  }
  orgStorage.setActiveOrgId(match.id);
  return match;
}
