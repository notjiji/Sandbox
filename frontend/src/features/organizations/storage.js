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
