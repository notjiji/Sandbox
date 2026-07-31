const ACTIVE_ORG_ID_KEY = "sandbox_active_org_id";

export const orgStorage = {
  setActiveOrgId(organizationId) {
    if (organizationId) {
      localStorage.setItem(ACTIVE_ORG_ID_KEY, organizationId);
    }
  },

  getActiveOrgId() {
    return localStorage.getItem(ACTIVE_ORG_ID_KEY);
  },

  clear() {
    localStorage.removeItem(ACTIVE_ORG_ID_KEY);
  },
};

function normalizeOrganizations(payload) {
  return payload?.data?.items ?? payload?.items ?? [];
}

/** Only organizations where the user has an active membership. */
export function getActiveOrganizations(payload) {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "active" && org.is_active,
  );
}

export function getInvitedOrganizations(payload) {
  return normalizeOrganizations(payload).filter(
    (org) => org.membership_status === "invited" && org.is_active,
  );
}

/**
 * Validate stored org id against server membership list.
 * Never trust a client-side org id without this check.
 */
export function resolveActiveOrganization(organizationsPayload) {
  const activeOrgs = getActiveOrganizations(organizationsPayload);
  if (!activeOrgs.length) {
    orgStorage.clear();
    return null;
  }

  const current = orgStorage.getActiveOrgId();
  const match = activeOrgs.find((org) => org.id === current);
  if (match) return match.id;

  orgStorage.setActiveOrgId(activeOrgs[0].id);
  return activeOrgs[0].id;
}

/** @deprecated use resolveActiveOrganization */
export function ensureActiveOrganization(organizationsPayload) {
  return resolveActiveOrganization(organizationsPayload);
}

export async function syncOrganizations(orgApi) {
  const payload = await orgApi.listMine();
  const activeOrgId = resolveActiveOrganization(payload);
  return {
    payload,
    activeOrgId,
    activeOrganizations: getActiveOrganizations(payload),
    invitedOrganizations: getInvitedOrganizations(payload),
  };
}

export function setValidatedActiveOrg(organizationId, organizationsPayload) {
  const activeOrgs = getActiveOrganizations(organizationsPayload);
  const match = activeOrgs.find((org) => org.id === organizationId);
  if (!match) {
    throw new Error("Organization not found in your active memberships");
  }
  orgStorage.setActiveOrgId(match.id);
  return match;
}
