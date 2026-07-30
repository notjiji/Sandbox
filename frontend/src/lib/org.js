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

/** Pick the first org from a list response and store it as active. */
export function ensureActiveOrganization(organizationsPayload) {
  const items = organizationsPayload?.data?.items ?? organizationsPayload?.items ?? [];
  if (!items.length) return null;

  const current = orgStorage.getActiveOrgId();
  const stillMember = items.some((org) => org.id === current);
  if (current && stillMember) return current;

  orgStorage.setActiveOrgId(items[0].id);
  return items[0].id;
}
