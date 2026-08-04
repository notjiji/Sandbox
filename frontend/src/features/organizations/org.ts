import { orgStorage } from "./storage";
import type { OrganizationListData, OrganizationSummary } from "@/shared/types/organization";

interface OrganizationsApiClient {
  listMine: () => Promise<OrganizationListData>;
}

function normalizeOrganizations(payload: OrganizationListData): OrganizationSummary[] {
  return payload.items ?? [];
}

/** Active organizations the user can switch into. */
export function getActiveOrganizations(payload: OrganizationListData): OrganizationSummary[] {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "active" && org.is_active,
  );
}

/** Archived organizations that can be restored by the owner. */
export function getArchivedOrganizations(payload: OrganizationListData): OrganizationSummary[] {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "active" && !org.is_active,
  );
}

export function getInvitedOrganizations(payload: OrganizationListData): OrganizationSummary[] {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "invited" && org.is_active,
  );
}

/**
 * Validate stored org id against server membership list.
 * Never trust a client-side org id without this check.
 */
export function resolveActiveOrganization(payload: OrganizationListData): string | null {
  const activeOrgs = getActiveOrganizations(payload);
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
  orgStorage.recordRecentOrg(firstOrg.id);
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
  organizationsPayload: OrganizationListData,
): OrganizationSummary {
  const activeOrgs = getActiveOrganizations(organizationsPayload);
  const match = activeOrgs.find((org) => org.id === organizationId);
  if (!match) {
    throw new Error("Organization not found in your active memberships");
  }
  orgStorage.setActiveOrgId(match.id);
  orgStorage.recordRecentOrg(match.id);
  return match;
}

/** Switch workspace after server-side membership validation. Persists last org in localStorage. */
export async function switchOrganization(
  api: OrganizationsApiClient,
  organizationId: string,
): Promise<OrganizationSummary> {
  const payload = await api.listMine();
  return setValidatedActiveOrg(organizationId, payload);
}
